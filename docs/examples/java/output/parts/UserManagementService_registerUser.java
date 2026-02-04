// code2map fragment (non-buildable)
// original: docs/examples/java/UserManagementService.java
// lines: 40-57
// symbol: UserManagementService#registerUser
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls users.containsKey, users.put, validateAge, validateEmail, validateUserId, validateUserName
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
