// code2map fragment (non-buildable)
// original: docs/examples/java/UserManagementService.java
// lines: 146-155
// symbol: UserManagementService#findByEmailDomain
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern; calls endsWith, result.add, user.getEmail, users.values
    public List<User> findByEmailDomain(String domain) {
        List<User> result = new ArrayList<>();
        String domainSuffix = "@" + domain;
        for (User user : users.values()) {
            if (user.getEmail().endsWith(domainSuffix)) {
                result.add(user);
            }
        }
        return result;
    }
