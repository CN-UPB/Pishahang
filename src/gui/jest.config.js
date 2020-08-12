module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  testPathIgnorePatterns: ["/node_modules/"],
  coveragePathIgnorePatterns: ["/node_modules/", "enzyme.js"],
  coverageReporters: ["json", "lcov", "text", "text-summary"],
};
