// code2map fragment (non-buildable)
// original: docs/examples/java/UserManagementService.java
// lines: 168-176
// symbol: UserManagementService#validateUserId
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls isEmpty, userId.length, userId.trim
    private void validateUserId(String userId) {
        if (userId == null || userId.trim().isEmpty()) {
            throw new IllegalArgumentException("ユーザーIDは必須です");
        }
        if (userId.length() > MAX_USER_ID_LENGTH) {
            throw new IllegalArgumentException(
                "ユーザーIDは" + MAX_USER_ID_LENGTH + "文字以内で入力してください");
        }
    }
