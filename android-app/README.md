# 🐄 LivestockAI Android Mobile Application

Native Android client for the **LivestockAI** marketplace & veterinary intelligence platform, built with **Kotlin**, **Jetpack Compose**, and **Material 3**.

---

## 📱 Features & Highlights

- 🔐 **JWT Token Authentication:** Buyer, Seller, and Admin registration & login with secure session storage.
- 🏪 **Livestock Marketplace:** Browse, live-search with debouncing, category chips (Cows, Dogs, Cats, Horses), price filters, and sorting.
- 🔍 **Animal Details Screen:** Photo gallery, breed/age/weight/milk specifications, vaccination badge, seller ratings, and direct **Buy Now** checkout.
- 🩺 **AI Veterinary Disease Scanner:** Take or upload animal photos to run instant symptom analysis and receive actionable medical, immediate-care, and home-remedy advice.
- 🤖 **Gemini Livestock Assistant:** Natural language AI chat specializing in Cow, Dog, Cat, and Horse care, diet, and live marketplace queries.
- 📍 **Nearby Mandis & Livestock:** Haversine distance-based discovery slider (10 km – 200 km) from user's location.
- ➕ **Seller Portal:** Multi-field livestock listing creation with image upload and health record snapshot.
- 📦 **Orders & Wishlist:** Track pending/paid orders and manage favorite livestock.

---

## 🏗️ Architecture & Technology Stack

- **UI Framework:** Jetpack Compose + Material 3 (Declarative UI)
- **Architecture:** MVVM (Model-View-ViewModel) + Repository Pattern + Clean Architecture
- **Networking:** Retrofit 2 + OkHttp 3 (with Auth & Logging Interceptors) + Gson
- **Image Loading:** Coil Compose
- **State Management:** Kotlin Coroutines + `StateFlow`
- **Local Persistence:** Encrypted / SharedPreferences TokenManager + Room Database ready
- **Hardware Integration:** CameraX & Gallery photo pickers, Geolocation GPS coordinates

---

## 🚀 How to Run the App

### Step 1: Start the Backend Flask Server
Open terminal in `d:\MINI_Project_3\VScode\LivestockAI`:
```bash
python wsgi.py
# Or run with python app.py
```
The REST API is available on `http://127.0.0.1:5000/api/v1/`.

### Step 2: Open & Run the Android Project in Android Studio
1. Launch **Android Studio**.
2. Select **Open** and select `d:\MINI_Project_3\android-app`.
3. Allow Gradle to sync dependencies.
4. Select an **Android Emulator** (or physical device over USB debugging).
5. Click **Run** (`Shift + F10`).

> [!NOTE]
> **Connecting Emulator to Host Backend:**  
> The Android emulator automatically routes `10.0.2.2:5000` to your host computer's `127.0.0.1:5000`.  
> For physical devices on the same Wi-Fi, change the base URL in [ApiClient.kt](file:///d:/MINI_Project_3/android-app/app/src/main/java/com/livestockai/app/data/api/ApiClient.kt) to your computer's local IP (e.g., `http://192.168.1.5:5000/`).

---

## 📂 Project Directory Structure

```
android-app/
├── app/
│   ├── build.gradle.kts
│   └── src/main/
│       ├── AndroidManifest.xml
│       └── java/com/livestockai/app/
│           ├── LivestockApplication.kt
│           ├── MainActivity.kt
│           ├── data/
│           │   ├── api/
│           │   │   ├── ApiClient.kt
│           │   │   ├── ApiService.kt
│           │   │   └── dto/ApiResponses.kt
│           │   ├── local/
│           │   │   └── TokenManager.kt
│           │   └── repository/
│           │       ├── AuthRepository.kt
│           │       ├── MarketplaceRepository.kt
│           │       ├── AIRepository.kt
│           │       └── OrderRepository.kt
│           ├── domain/model/
│           │   ├── User.kt
│           │   ├── Animal.kt
│           │   ├── DiagnosisResult.kt
│           │   └── Order.kt
│           └── ui/
│               ├── theme/ (Color.kt, Type.kt, Theme.kt)
│               ├── navigation/ (Screen.kt, NavGraph.kt)
│               ├── components/ (AnimalCard.kt, SearchBar.kt, BottomNavBar.kt)
│               └── screens/
│                   ├── auth/ (LoginScreen.kt, RegisterScreen.kt, AuthViewModel.kt)
│                   ├── home/ (HomeScreen.kt, HomeViewModel.kt)
│                   ├── marketplace/ (MarketplaceScreen.kt, AnimalDetailScreen.kt, MarketplaceViewModel.kt)
│                   ├── scanner/ (DiseaseScannerScreen.kt, DiseaseScannerViewModel.kt)
│                   ├── ai/ (AIChatScreen.kt, AIChatViewModel.kt)
│                   ├── sell/ (AddListingScreen.kt, AddListingViewModel.kt)
│                   ├── profile/ (ProfileScreen.kt)
│                   ├── orders/ (OrdersScreen.kt)
│                   ├── wishlist/ (WishlistScreen.kt)
│                   └── map/ (NearbyMapScreen.kt)
├── build.gradle.kts
├── settings.gradle.kts
└── gradle/
    └── libs.versions.toml
```
