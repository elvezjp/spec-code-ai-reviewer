package com.example.order;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;

/**
 * 注文キャンセルAPI のサービスクラス。
 * POST /orders/{orderId}/cancel から呼び出される。
 */
public class CancelOrderService {

    /** キャンセル期限（時間） */
    private static final long CANCEL_LIMIT_HOURS = 48;

    /** 受け付けるキャンセル理由コード */
    private static final List<String> VALID_REASON_CODES = Arrays.asList("C01", "C02", "C03", "C04");

    /** 理由コードが判定できない場合に適用する既定コード（C04: その他） */
    private static final String DEFAULT_REASON_CODE = "C04";

    private final OrderRepository orderRepository;
    private final RefundService refundService;
    private final InventoryService inventoryService;

    public CancelOrderService(OrderRepository orderRepository,
                              RefundService refundService,
                              InventoryService inventoryService) {
        this.orderRepository = orderRepository;
        this.refundService = refundService;
        this.inventoryService = inventoryService;
    }

    /**
     * 注文キャンセルを受け付ける。
     *
     * @param request キャンセル要求
     * @return キャンセル結果
     */
    public CancelResult cancel(CancelRequest request) {
        if (request == null || isBlank(request.getOrderId())) {
            return CancelResult.error("E-400", "リクエストが不正です");
        }

        String reasonCode = normalizeReasonCode(request.getReasonCode());

        Order order = orderRepository.findById(request.getOrderId());
        if (order == null) {
            return CancelResult.error("E-404", "注文が見つかりません");
        }

        // すでにキャンセル済みの場合は結果が変わらないため、成功として扱う
        if (order.getStatus() == OrderStatus.CANCELLED) {
            return CancelResult.accepted(order.getOrderId(), 0L);
        }

        // 配送済みの注文はキャンセル不可
        if (order.getStatus() == OrderStatus.SHIPPED) {
            return CancelResult.error("E-409", "配送済みのためキャンセルできません");
        }

        // ゴールド会員はキャンセル期限の対象外とする
        if (!"GOLD".equals(order.getMemberRank())) {
            Duration elapsed = Duration.between(order.getConfirmedAt(), LocalDateTime.now());
            if (elapsed.toHours() > CANCEL_LIMIT_HOURS) {
                return CancelResult.error("E-500", "キャンセルできませんでした");
            }
        }

        long refundedAmount = 0L;
        if (order.isPaid()) {
            refundedAmount = calculateRefundAmount(order);
            refundService.refund(order.getPaymentId(), refundedAmount);
        }

        releaseInventory(order);

        order.setStatus(OrderStatus.CANCELLED);
        order.setCancelReasonCode(reasonCode);
        orderRepository.save(order);

        return CancelResult.accepted(order.getOrderId(), refundedAmount);
    }

    /**
     * キャンセル理由コードを正規化する。
     * 判定できないコードは既定コード（C04: その他）として扱う。
     */
    private String normalizeReasonCode(String reasonCode) {
        if (reasonCode == null) {
            return DEFAULT_REASON_CODE;
        }
        String trimmed = reasonCode.trim();
        if (VALID_REASON_CODES.contains(trimmed)) {
            return trimmed;
        }
        return DEFAULT_REASON_CODE;
    }

    /**
     * 返金額を算出する。
     */
    private long calculateRefundAmount(Order order) {
        long refundAmount = order.getItemTotal() + order.getShippingFee();
        // ポイント利用分は返金額から差し引く
        refundAmount -= order.getUsedPoints();
        if (refundAmount < 0) {
            refundAmount = 0;
        }
        return refundAmount;
    }

    /**
     * 注文明細のすべての商品について引当在庫を解放する。
     */
    private void releaseInventory(Order order) {
        for (OrderLine line : order.getLines()) {
            inventoryService.release(line.getProductCode(), line.getQuantity());
        }
    }

    private static boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }
}

/**
 * キャンセル要求。リクエストボディの内容を保持する。
 */
class CancelRequest {

    private final String orderId;
    private final String reasonCode;
    private final String operatorId;

    CancelRequest(String orderId, String reasonCode, String operatorId) {
        this.orderId = orderId;
        this.reasonCode = reasonCode;
        this.operatorId = operatorId;
    }

    String getOrderId() {
        return orderId;
    }

    String getReasonCode() {
        return reasonCode;
    }

    String getOperatorId() {
        return operatorId;
    }
}

/**
 * キャンセル結果。API 応答の生成元となる。
 */
class CancelResult {

    private final boolean accepted;
    private final String orderId;
    private final String errorCode;
    private final String message;
    private final long refundedAmount;

    private CancelResult(boolean accepted, String orderId, String errorCode,
                         String message, long refundedAmount) {
        this.accepted = accepted;
        this.orderId = orderId;
        this.errorCode = errorCode;
        this.message = message;
        this.refundedAmount = refundedAmount;
    }

    static CancelResult accepted(String orderId, long refundedAmount) {
        return new CancelResult(true, orderId, null, null, refundedAmount);
    }

    static CancelResult error(String errorCode, String message) {
        return new CancelResult(false, null, errorCode, message, 0L);
    }

    boolean isAccepted() {
        return accepted;
    }

    String getOrderId() {
        return orderId;
    }

    String getErrorCode() {
        return errorCode;
    }

    String getMessage() {
        return message;
    }

    long getRefundedAmount() {
        return refundedAmount;
    }
}

/**
 * 注文ステータス。
 */
enum OrderStatus {
    /** 注文確定 */
    CONFIRMED,
    /** 支払済み */
    PAID,
    /** 配送済み */
    SHIPPED,
    /** 配達完了 */
    DELIVERED,
    /** キャンセル済み */
    CANCELLED
}

/**
 * 注文。
 */
class Order {

    private final String orderId;
    private final String memberRank;
    private final LocalDateTime confirmedAt;
    private final boolean paid;
    private final String paymentId;
    private final long itemTotal;
    private final long shippingFee;
    private final long usedPoints;
    private final List<OrderLine> lines;
    private OrderStatus status;
    private String cancelReasonCode;

    Order(String orderId, String memberRank, LocalDateTime confirmedAt,
          boolean paid, String paymentId, long itemTotal, long shippingFee,
          long usedPoints, List<OrderLine> lines, OrderStatus status) {
        this.orderId = orderId;
        this.memberRank = memberRank;
        this.confirmedAt = confirmedAt;
        this.paid = paid;
        this.paymentId = paymentId;
        this.itemTotal = itemTotal;
        this.shippingFee = shippingFee;
        this.usedPoints = usedPoints;
        this.lines = lines;
        this.status = status;
    }

    String getOrderId() {
        return orderId;
    }

    String getMemberRank() {
        return memberRank;
    }

    LocalDateTime getConfirmedAt() {
        return confirmedAt;
    }

    boolean isPaid() {
        return paid;
    }

    String getPaymentId() {
        return paymentId;
    }

    long getItemTotal() {
        return itemTotal;
    }

    long getShippingFee() {
        return shippingFee;
    }

    long getUsedPoints() {
        return usedPoints;
    }

    List<OrderLine> getLines() {
        return lines;
    }

    OrderStatus getStatus() {
        return status;
    }

    void setStatus(OrderStatus status) {
        this.status = status;
    }

    String getCancelReasonCode() {
        return cancelReasonCode;
    }

    void setCancelReasonCode(String cancelReasonCode) {
        this.cancelReasonCode = cancelReasonCode;
    }
}

/**
 * 注文明細（1商品分）。
 */
class OrderLine {

    private final String productCode;
    private final int quantity;

    OrderLine(String productCode, int quantity) {
        this.productCode = productCode;
        this.quantity = quantity;
    }

    String getProductCode() {
        return productCode;
    }

    int getQuantity() {
        return quantity;
    }
}

/**
 * 注文リポジトリ。
 */
interface OrderRepository {

    Order findById(String orderId);

    void save(Order order);
}

/**
 * 返金サービス。決済基盤への返金指示を行う。
 */
interface RefundService {

    void refund(String paymentId, long amount);
}

/**
 * 在庫サービス。引当在庫の解放を行う。
 */
interface InventoryService {

    void release(String productCode, int quantity);
}
