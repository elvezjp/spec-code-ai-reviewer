// code2map fragment (non-buildable)
// id: CD3
// original: docs/examples/java/UserManagementService.java
// lines: 69-89
// symbol: UserManagementService#updateUser
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls email.isEmpty, existingUser.setAge, existingUser.setEmail, existingUser.setUserName, findUserOrThrow, userName.isEmpty, validateAge, validateEmail, validateUserName
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
