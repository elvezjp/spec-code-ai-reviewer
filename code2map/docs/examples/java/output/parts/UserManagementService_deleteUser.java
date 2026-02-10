// code2map fragment (non-buildable)
// id: CD4
// original: docs/examples/java/UserManagementService.java
// lines: 98-102
// symbol: UserManagementService#deleteUser
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls findUserOrThrow, users.remove
    public User deleteUser(String userId) {
        User existingUser = findUserOrThrow(userId);
        users.remove(userId);
        return existingUser;
    }
