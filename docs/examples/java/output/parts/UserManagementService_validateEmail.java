// code2map fragment (non-buildable)
// original: docs/examples/java/UserManagementService.java
// lines: 188-195
// symbol: UserManagementService#validateEmail
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls EMAIL_PATTERN.matcher, email.trim, isEmpty, matches
    private void validateEmail(String email) {
        if (email == null || email.trim().isEmpty()) {
            throw new IllegalArgumentException("メールアドレスは必須です");
        }
        if (!EMAIL_PATTERN.matcher(email).matches()) {
            throw new IllegalArgumentException("メールアドレスの形式が不正です");
        }
    }
