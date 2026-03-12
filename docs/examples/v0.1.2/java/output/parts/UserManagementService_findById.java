// code2map fragment (non-buildable)
// id: CD5
// original: docs/examples/java/UserManagementService.java
// lines: 110-112
// symbol: UserManagementService#findById
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls Optional.ofNullable, users.get
    public Optional<User> findById(String userId) {
        return Optional.ofNullable(users.get(userId));
    }
