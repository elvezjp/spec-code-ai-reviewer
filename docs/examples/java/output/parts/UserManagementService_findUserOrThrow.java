// code2map fragment (non-buildable)
// original: docs/examples/java/UserManagementService.java
// lines: 203-209
// symbol: UserManagementService#findUserOrThrow
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls users.get
    private User findUserOrThrow(String userId) {
        User user = users.get(userId);
        if (user == null) {
            throw new UserNotFoundException("ユーザーID '" + userId + "' が見つかりません");
        }
        return user;
    }
