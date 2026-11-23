pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
// Gradle's supported centralized repository API is still annotated @Incubating.
@Suppress("UnstableApiUsage")
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "FinCalc"
include(":app")
