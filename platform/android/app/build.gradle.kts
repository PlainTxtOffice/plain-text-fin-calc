import java.util.Properties

plugins { alias(libs.plugins.android.application) }

// Release signing details stay out of version control. Without keystore.properties
// the release build is unsigned, so the project still builds from public source.
val keystoreProperties = Properties().apply {
    val file = rootProject.file("keystore.properties")
    if (file.isFile) file.inputStream().use(::load)
}
val releaseStoreFile = keystoreProperties.getProperty("storeFile").orEmpty()

android {
    namespace = "com.plaintxtoffice.fincalc"
    compileSdk = 37
    defaultConfig {
        applicationId = "com.plaintxtoffice.fincalc"
        minSdk = 26
        // Keep the validated API 36 behavior; an API 37 target migration needs separate device testing.
        //noinspection AndroidLintOldTargetApi
        targetSdk = 36
        versionCode = 7
        versionName = "0.5.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    buildFeatures { buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    signingConfigs {
        if (releaseStoreFile.isNotBlank()) {
            create("release") {
                storeFile = rootProject.file(releaseStoreFile)
                storePassword = keystoreProperties.getProperty("storePassword")
                keyAlias = keystoreProperties.getProperty("keyAlias")
                keyPassword = keystoreProperties.getProperty("keyPassword")
            }
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.findByName("release")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
        }
    }
}

// Names outputs with the app and version, such as plain-text-fin-calc-0.5.0-7-release.aab,
// instead of app-release.aab. Must come after android { } because it reads
// defaultConfig.
base {
    archivesName = "plain-text-fin-calc-${android.defaultConfig.versionName}-${android.defaultConfig.versionCode}"
}

dependencies {
    implementation(libs.androidx.activity.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.ktx)
    implementation(libs.androidx.recyclerview)
    implementation(libs.gson)
    testImplementation(libs.junit)
}
