// code2map fragment (non-buildable)
// original: docs/examples/java/UserManagementService.java
// lines: 119-121
// symbol: UserManagementService#findAll
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls users.values
    public List<User> findAll() {
        return new ArrayList<>(users.values());
    }
