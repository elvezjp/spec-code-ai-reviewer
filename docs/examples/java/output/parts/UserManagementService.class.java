// code2map fragment (non-buildable)
// id: CD1
// original: docs/examples/java/UserManagementService.java
// lines: 14-210
// symbol: UserManagementService
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern
public class UserManagementService {

    /** ユーザー格納用のマップ（キー: ユーザーID） */
    private final Map<String, User> users = new HashMap<>();

    /** メールアドレスの正規表現パターン */
    private static final Pattern EMAIL_PATTERN =
        Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$");

    /** ユーザーIDの最大長 */
    private static final int MAX_USER_ID_LENGTH = 20;

    /** ユーザー名の最大長 */
    private static final int MAX_USER_NAME_LENGTH = 50;

    /**
     * 新規ユーザーを登録する
     *
     * @param userId ユーザーID（必須、20文字以内）
     * @param userName ユーザー名（必須、50文字以内）
     * @param email メールアドレス（必須、形式チェックあり）
     * @param age 年齢（0以上150以下）
     * @return 登録されたユーザー
     * @throws IllegalArgumentException 入力値が不正な場合
     * @throws UserAlreadyExistsException 同一IDのユーザーが既に存在する場合
     */
    public User registerUser(String userId, String userName, String email, int age) {
        // 入力値検証
        validateUserId(userId);
        validateUserName(userName);
        validateEmail(email);
        validateAge(age);

        // 重複チェック
        if (users.containsKey(userId)) {
            throw new UserAlreadyExistsException("ユーザーID '" + userId + "' は既に登録されています");
        }

        // ユーザー作成・登録
        User newUser = new User(userId, userName, email, age);
        users.put(userId, newUser);

        return newUser;
    }

    /**
     * ユーザー情報を更新する
     *
     * @param userId 更新対象のユーザーID
     * @param userName 新しいユーザー名（nullの場合は更新しない）
     * @param email 新しいメールアドレス（nullの場合は更新しない）
     * @param age 新しい年齢（負の値の場合は更新しない）
     * @return 更新されたユーザー
     * @throws UserNotFoundException ユーザーが見つからない場合
     */
    public User updateUser(String userId, String userName, String email, int age) {
        User existingUser = findUserOrThrow(userId);

        // 各フィールドの更新（nullや負値でない場合のみ）
        if (userName != null && !userName.isEmpty()) {
            validateUserName(userName);
            existingUser.setUserName(userName);
        }

        if (email != null && !email.isEmpty()) {
            validateEmail(email);
            existingUser.setEmail(email);
        }

        if (age >= 0) {
            validateAge(age);
            existingUser.setAge(age);
        }

        return existingUser;
    }

    /**
     * ユーザーを削除する
     *
     * @param userId 削除対象のユーザーID
     * @return 削除されたユーザー
     * @throws UserNotFoundException ユーザーが見つからない場合
     */
    public User deleteUser(String userId) {
        User existingUser = findUserOrThrow(userId);
        users.remove(userId);
        return existingUser;
    }

    /**
     * ユーザーIDでユーザーを検索する
     *
     * @param userId 検索対象のユーザーID
     * @return 見つかったユーザー（Optional）
     */
    public Optional<User> findById(String userId) {
        return Optional.ofNullable(users.get(userId));
    }

    /**
     * 全ユーザーを取得する
     *
     * @return 全ユーザーのリスト
     */
    public List<User> findAll() {
        return new ArrayList<>(users.values());
    }

    /**
     * 年齢範囲でユーザーを検索する
     *
     * @param minAge 最小年齢（含む）
     * @param maxAge 最大年齢（含む）
     * @return 条件に一致するユーザーのリスト
     */
    public List<User> findByAgeRange(int minAge, int maxAge) {
        List<User> result = new ArrayList<>();
        for (User user : users.values()) {
            if (user.getAge() >= minAge && user.getAge() <= maxAge) {
                result.add(user);
            }
        }
        return result;
    }

    /**
     * メールドメインでユーザーを検索する
     *
     * @param domain メールドメイン（例: "example.com"）
     * @return 条件に一致するユーザーのリスト
     */
    public List<User> findByEmailDomain(String domain) {
        List<User> result = new ArrayList<>();
        String domainSuffix = "@" + domain;
        for (User user : users.values()) {
            if (user.getEmail().endsWith(domainSuffix)) {
                result.add(user);
            }
        }
        return result;
    }

    /**
     * 登録ユーザー数を取得する
     *
     * @return 登録ユーザー数
     */
    public int getUserCount() {
        return users.size();
    }

    // --- バリデーションメソッド ---

    private void validateUserId(String userId) {
        if (userId == null || userId.trim().isEmpty()) {
            throw new IllegalArgumentException("ユーザーIDは必須です");
        }
        if (userId.length() > MAX_USER_ID_LENGTH) {
            throw new IllegalArgumentException(
                "ユーザーIDは" + MAX_USER_ID_LENGTH + "文字以内で入力してください");
        }
    }

    private void validateUserName(String userName) {
        if (userName == null || userName.trim().isEmpty()) {
            throw new IllegalArgumentException("ユーザー名は必須です");
        }
        if (userName.length() > MAX_USER_NAME_LENGTH) {
            throw new IllegalArgumentException(
                "ユーザー名は" + MAX_USER_NAME_LENGTH + "文字以内で入力してください");
        }
    }

    private void validateEmail(String email) {
        if (email == null || email.trim().isEmpty()) {
            throw new IllegalArgumentException("メールアドレスは必須です");
        }
        if (!EMAIL_PATTERN.matcher(email).matches()) {
            throw new IllegalArgumentException("メールアドレスの形式が不正です");
        }
    }

    private void validateAge(int age) {
        if (age < 0 || age > 150) {
            throw new IllegalArgumentException("年齢は0以上150以下で入力してください");
        }
    }

    private User findUserOrThrow(String userId) {
        User user = users.get(userId);
        if (user == null) {
            throw new UserNotFoundException("ユーザーID '" + userId + "' が見つかりません");
        }
        return user;
    }
}
