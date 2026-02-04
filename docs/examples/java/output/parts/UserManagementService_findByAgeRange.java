// code2map fragment (non-buildable)
// original: docs/examples/java/UserManagementService.java
// lines: 130-138
// symbol: UserManagementService#findByAgeRange
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls result.add, user.getAge, users.values
    public List<User> findByAgeRange(int minAge, int maxAge) {
        List<User> result = new ArrayList<>();
        for (User user : users.values()) {
            if (user.getAge() >= minAge && user.getAge() <= maxAge) {
                result.add(user);
            }
        }
        return result;
    }
