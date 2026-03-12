public class Java8Syntax {
    enum Status {
        A("a");
        private final String key;
        Status(String key) { this.key = key; }
        public String[] getKeys() {
            return java.util.Arrays.stream(Status.values())
                .map(Status::name).toArray(String[]::new);
        }
    }
}
