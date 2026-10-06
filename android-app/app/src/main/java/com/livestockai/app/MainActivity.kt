package com.livestockai.app

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import android.view.View
import android.webkit.*
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.livestockai.app.ui.theme.LivestockAITheme
import com.livestockai.app.ui.theme.PrimaryGreen
import java.io.File

class MainActivity : ComponentActivity() {

    private var fileUploadCallback: ValueCallback<Array<Uri>>? = null
    private var webView: WebView? = null

    // Native Image/Camera Upload Launcher for WebView forms (Disease Scanner & Animal Listing)
    private val fileChooserLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (fileUploadCallback == null) return@registerForActivityResult
        var results: Array<Uri>? = null
        if (result.resultCode == RESULT_OK) {
            val data = result.data
            if (data != null && data.data != null) {
                results = arrayOf(data.data!!)
            } else if (data?.clipData != null) {
                val count = data.clipData!!.itemCount
                val uris = mutableListOf<Uri>()
                for (i in 0 until count) {
                    uris.add(data.clipData!!.getItemAt(i).uri)
                }
                results = uris.toTypedArray()
            }
        }
        fileUploadCallback?.onReceiveValue(results)
        fileUploadCallback = null
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val prefs = getSharedPreferences("livestock_webview_prefs", Context.MODE_PRIVATE)
        val defaultUrl = prefs.getString("server_url", "http://192.168.1.18:5000/") ?: "http://192.168.1.18:5000/"

        setContent {
            LivestockAITheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    LivestockWebViewApp(
                        initialUrl = defaultUrl,
                        onSaveServerUrl = { newUrl ->
                            prefs.edit().putString("server_url", newUrl).apply()
                        },
                        onOpenFileChooser = { callback, intent ->
                            fileUploadCallback = callback
                            fileChooserLauncher.launch(intent)
                        },
                        onWebViewCreated = { wv ->
                            webView = wv
                        }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LivestockWebViewApp(
    initialUrl: String,
    onSaveServerUrl: (String) -> Unit,
    onOpenFileChooser: (ValueCallback<Array<Uri>>, Intent) -> Unit,
    onWebViewCreated: (WebView) -> Unit
) {
    var currentUrl by remember { mutableStateOf(initialUrl) }
    var inputUrl by remember { mutableStateOf(initialUrl) }
    var isLoading by remember { mutableStateOf(true) }
    var progress by remember { mutableFloatStateOf(0f) }
    var isError by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }
    var showSettingsDialog by remember { mutableStateOf(false) }
    var canGoBack by remember { mutableStateOf(false) }
    var canGoForward by remember { mutableStateOf(false) }
    var activeWebView by remember { mutableStateOf<WebView?>(null) }

    val context = LocalContext.current

    // Request permissions for camera, location, and storage
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { }

    LaunchedEffect(Unit) {
        val permissions = mutableListOf(
            Manifest.permission.CAMERA,
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.S_V2) {
            permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
        }
        permissionLauncher.launch(permissions.toTypedArray())
    }

    // Handle System Back Button to navigate inside WebView history
    BackHandler(enabled = canGoBack) {
        activeWebView?.goBack()
    }

    Scaffold(
        modifier = Modifier.fillMaxSize()
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Main Android WebView Component
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { ctx ->
                    WebView(ctx).apply {
                        configureWebViewSettings(this)

                        webViewClient = object : WebViewClient() {
                            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                                super.onPageStarted(view, url, favicon)
                                isLoading = true
                                isError = false
                                url?.let { currentUrl = it }
                                canGoBack = view?.canGoBack() == true
                                canGoForward = view?.canGoForward() == true
                            }

                            override fun onPageFinished(view: WebView?, url: String?) {
                                super.onPageFinished(view, url)
                                isLoading = false
                                url?.let { currentUrl = it }
                                canGoBack = view?.canGoBack() == true
                                canGoForward = view?.canGoForward() == true
                            }

                            override fun onReceivedError(
                                view: WebView?,
                                request: WebResourceRequest?,
                                error: WebResourceError?
                            ) {
                                super.onReceivedError(view, request, error)
                                if (request?.isForMainFrame == true) {
                                    isError = true
                                    isLoading = false
                                    errorMessage = error?.description?.toString() ?: "Failed to connect to LivestockAI server."
                                }
                            }

                            override fun shouldOverrideUrlLoading(
                                view: WebView?,
                                request: WebResourceRequest?
                            ): Boolean {
                                val url = request?.url?.toString() ?: return false
                                return if (url.startsWith("http://") || url.startsWith("https://")) {
                                    false // Load inside WebView
                                } else {
                                    try {
                                        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                                        ctx.startActivity(intent)
                                        true
                                    } catch (e: Exception) {
                                        true
                                    }
                                }
                            }
                        }

                        webChromeClient = object : WebChromeClient() {
                            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                                progress = newProgress / 100f
                            }

                            override fun onPermissionRequest(request: PermissionRequest?) {
                                request?.grant(request.resources)
                            }

                            override fun onShowFileChooser(
                                webView: WebView?,
                                filePathCallback: ValueCallback<Array<Uri>>?,
                                fileChooserParams: FileChooserParams?
                            ): Boolean {
                                if (filePathCallback == null) return false
                                val intent = fileChooserParams?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT).apply {
                                    type = "image/*"
                                    putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
                                }
                                onOpenFileChooser(filePathCallback, intent)
                                return true
                            }

                            override fun onGeolocationPermissionsShowPrompt(
                                origin: String?,
                                callback: GeolocationPermissions.Callback?
                            ) {
                                callback?.invoke(origin, true, false)
                            }
                        }

                        onWebViewCreated(this)
                        activeWebView = this
                        loadUrl(currentUrl)
                    }
                },
                update = { wv ->
                    activeWebView = wv
                }
            )

            // Top Linear Loading Progress Bar
            if (isLoading) {
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier
                        .fillMaxWidth()
                        .align(Alignment.TopCenter),
                    color = PrimaryGreen,
                    trackColor = Color.Transparent
                )
            }

            // Connection Error & Offline Retry Screen
            if (isError) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Surface(
                            modifier = Modifier.size(70.dp),
                            shape = CircleShape,
                            color = MaterialTheme.colorScheme.errorContainer
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = Icons.Filled.WifiOff,
                                    contentDescription = "Connection Error",
                                    tint = MaterialTheme.colorScheme.onErrorContainer,
                                    modifier = Modifier.size(36.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        Text(
                            text = "Cannot Connect to LivestockAI",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )

                        Text(
                            text = "Target Server: $currentUrl\n\nError: $errorMessage",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(top = 8.dp, bottom = 20.dp)
                        )

                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            Button(
                                onClick = {
                                    isError = false
                                    activeWebView?.loadUrl(currentUrl)
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen)
                            ) {
                                Icon(Icons.Filled.Refresh, contentDescription = "Retry")
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Retry Connection")
                            }

                            OutlinedButton(onClick = { showSettingsDialog = true }) {
                                Icon(Icons.Filled.Settings, contentDescription = "Change IP")
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Change IP")
                            }
                        }
                    }
                }
            }
        }
    }

    // Change Server IP Dialog
    if (showSettingsDialog) {
        AlertDialog(
            onDismissRequest = { showSettingsDialog = false },
            title = { Text("Server Connection URL") },
            text = {
                Column {
                    Text(
                        text = "Enter your computer's local IP or backend URL:",
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                    OutlinedTextField(
                        value = inputUrl,
                        onValueChange = { inputUrl = it },
                        label = { Text("Server URL") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Text("Quick Presets:", style = MaterialTheme.typography.labelSmall)
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        FilterChip(
                            selected = inputUrl.contains("192.168.1.18"),
                            onClick = { inputUrl = "http://192.168.1.18:5000/" },
                            label = { Text("192.168.1.18") }
                        )
                        FilterChip(
                            selected = inputUrl.contains("10.0.2.2"),
                            onClick = { inputUrl = "http://10.0.2.2:5000/" },
                            label = { Text("Emulator (10.0.2.2)") }
                        )
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val formatted = if (inputUrl.endsWith("/")) inputUrl else "$inputUrl/"
                        onSaveServerUrl(formatted)
                        currentUrl = formatted
                        showSettingsDialog = false
                        isError = false
                        activeWebView?.loadUrl(formatted)
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen)
                ) {
                    Text("Connect")
                }
            },
            dismissButton = {
                TextButton(onClick = { showSettingsDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@SuppressLint("SetJavaScriptEnabled")
private fun configureWebViewSettings(webView: WebView) {
    webView.settings.apply {
        // Core features for modern web apps
        javaScriptEnabled = true
        domStorageEnabled = true
        databaseEnabled = true
        
        // Window & UI features
        javaScriptCanOpenWindowsAutomatically = true
        setSupportMultipleWindows(false)
        loadWithOverviewMode = false // Do NOT minimize/zoom out to desktop mode
        useWideViewPort = false      // Force 100% native mobile screen width
        textZoom = 100               // 100% text scale
        
        // Zoom settings
        setSupportZoom(false)        // Prevent accidental user zooming
        builtInZoomControls = false
        displayZoomControls = false
        
        // File & Media
        allowFileAccess = true
        allowContentAccess = true
        mediaPlaybackRequiresUserGesture = false
        
        // Security & Network
        mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        cacheMode = WebSettings.LOAD_DEFAULT
        
        // Crucial: Use a standard mobile Chrome User Agent
        // This prevents the website from thinking it's a "limited" WebView
        val chromeUserAgent = "Mozilla/5.0 (Linux; Android ${Build.VERSION.RELEASE}; ${Build.MODEL}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        userAgentString = chromeUserAgent
    }
    
    // Enable Hardware Acceleration for smooth UI/Menus
    webView.setLayerType(View.LAYER_TYPE_HARDWARE, null)
    
    // Cookie management
    val cookieManager = CookieManager.getInstance()
    cookieManager.setAcceptCookie(true)
    cookieManager.setAcceptThirdPartyCookies(webView, true)
}
