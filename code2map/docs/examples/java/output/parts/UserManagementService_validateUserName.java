// code2map fragment (non-buildable)
// original: docs/examples/java/UserManagementService.java
// lines: 178-186
// symbol: UserManagementService#validateUserName
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls isEmpty, userName.length, userName.trim
    private void validateUserName(String userName) {
        if (userName == null || userName.trim().isEmpty()) {
            throw new IllegalArgumentException("ユーザー名は必須です");
        }
        if (userName.length() > MAX_USER_NAME_LENGTH) {
            throw new IllegalArgumentException(
                "ユーザー名は" + MAX_USER_NAME_LENGTH + "文字以内で入力してください");
        }
    }
