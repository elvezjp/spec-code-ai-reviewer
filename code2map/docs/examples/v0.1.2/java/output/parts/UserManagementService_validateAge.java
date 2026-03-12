// code2map fragment (non-buildable)
// id: CD13
// original: docs/examples/java/UserManagementService.java
// lines: 197-201
// symbol: UserManagementService#validateAge
// notes: references java.util.ArrayList, java.util.HashMap, java.util.List, java.util.Map, java.util.Optional, java.util.regex.Pattern
    private void validateAge(int age) {
        if (age < 0 || age > 150) {
            throw new IllegalArgumentException("年齢は0以上150以下で入力してください");
        }
    }
