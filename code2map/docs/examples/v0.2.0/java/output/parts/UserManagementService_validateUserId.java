// code2map fragment (non-buildable)
// id: CD10
// original: docs/examples/v0.2.0/java/UserManagementService.java
// lines: 168-176
// symbol: UserManagementService#validateUserId
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls userId.length, userId.trim, userId.trim().isEmpty
    private void validateUserId(String userId) {
        if (userId == null || userId.trim().isEmpty()) {
            throw new IllegalArgumentException("ユーザーIDは必須です");
        }
        if (userId.length() > MAX_USER_ID_LENGTH) {
            throw new IllegalArgumentException(
                "ユーザーIDは" + MAX_USER_ID_LENGTH + "文字以内で入力してください");
        }
    }
