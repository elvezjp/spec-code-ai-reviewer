// code2map fragment (non-buildable)
// id: CD15
// original: docs/examples/java/UserManagementService.java
// lines: 215-235
// symbol: User
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern
class User {
    private final String userId;
    private String userName;
    private String email;
    private int age;

    public User(String userId, String userName, String email, int age) {
        this.userId = userId;
        this.userName = userName;
        this.email = email;
        this.age = age;
    }

    public String getUserId() { return userId; }
    public String getUserName() { return userName; }
    public void setUserName(String userName) { this.userName = userName; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public int getAge() { return age; }
    public void setAge(int age) { this.age = age; }
}
