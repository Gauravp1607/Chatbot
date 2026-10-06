package com.livestockai.app.ui.screens.scanner

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.livestockai.app.domain.model.DiagnosisResult
import com.livestockai.app.ui.theme.*
import java.io.File
import java.io.FileOutputStream

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiseaseScannerScreen(
    viewModel: DiseaseScannerViewModel,
    onNavigateToAIChat: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scannerState by viewModel.scannerState.collectAsState()
    val context = LocalContext.current

    val imagePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            val file = copyUriToFile(context, it)
            if (file != null) {
                viewModel.onImageSelected(it, file)
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "AI Veterinary Health Scanner",
                        fontWeight = FontWeight.Bold
                    )
                }
            )
        }
    ) { padding ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            when (val state = scannerState) {
                is ScannerState.Idle -> {
                    // Upload / Capture Box
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(280.dp)
                            .clip(RoundedCornerShape(20.dp))
                            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f))
                            .border(2.dp, PrimaryGreen.copy(alpha = 0.4f), RoundedCornerShape(20.dp))
                            .clickable { imagePickerLauncher.launch("image/*") },
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.padding(24.dp)
                        ) {
                            Surface(
                                modifier = Modifier.size(70.dp),
                                shape = CircleShape,
                                color = PrimaryGreen.copy(alpha = 0.1f)
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        imageVector = Icons.Filled.AddPhotoAlternate,
                                        contentDescription = "Upload Photo",
                                        tint = PrimaryGreen,
                                        modifier = Modifier.size(36.dp)
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(16.dp))

                            Text(
                                text = "Take or Upload Animal Photo",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )

                            Text(
                                text = "Supported: Cows, Dogs, Cats, Horses\n(Skin lesions, eyes, ticks, mouth)",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                textAlign = TextAlign.Center,
                                modifier = Modifier.padding(top = 6.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    Button(
                        onClick = { imagePickerLauncher.launch("image/*") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen)
                    ) {
                        Icon(Icons.Filled.CameraAlt, contentDescription = "Camera")
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Select Photo to Diagnose", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                    }
                }

                is ScannerState.ImageSelected -> {
                    // Image Preview + Start Diagnosis Button
                    AsyncImage(
                        model = state.imageUri,
                        contentDescription = "Selected Animal",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(280.dp)
                            .clip(RoundedCornerShape(20.dp)),
                        contentScale = ContentScale.Crop
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        OutlinedButton(
                            onClick = { viewModel.reset() },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Retake")
                        }

                        Button(
                            onClick = { viewModel.startScan() },
                            modifier = Modifier.weight(2f),
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen)
                        ) {
                            Icon(Icons.Filled.AutoAwesome, contentDescription = "Scan")
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("Run AI Diagnosis", fontWeight = FontWeight.Bold)
                        }
                    }
                }

                is ScannerState.Scanning -> {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(300.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator(
                                color = PrimaryGreen,
                                strokeWidth = 4.dp,
                                modifier = Modifier.size(60.dp)
                            )
                            Spacer(modifier = Modifier.height(20.dp))
                            Text(
                                text = "Analyzing symptoms with VetAI Model...",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = "Evaluating lesion patterns and disease database",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.padding(top = 4.dp)
                            )
                        }
                    }
                }

                is ScannerState.Success -> {
                    DiagnosisResultCard(
                        result = state.result,
                        onScanAgain = { viewModel.reset() },
                        onAskAI = onNavigateToAIChat
                    )
                }

                is ScannerState.Error -> {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(14.dp),
                        color = MaterialTheme.colorScheme.errorContainer
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Diagnosis Error",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onErrorContainer
                            )
                            Text(
                                text = state.message,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
                            )
                            Button(
                                onClick = { viewModel.reset() },
                                colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen)
                            ) {
                                Text("Try Again")
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun DiagnosisResultCard(
    result: DiagnosisResult,
    onScanAgain: () -> Unit,
    onAskAI: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            // Header Diagnosis Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = if (result.severity.equals("Critical", true) || result.severity.equals("High", true)) StatusError else AmberAccent
                ) {
                    Text(
                        text = "Severity: ${result.severity}",
                        color = Color.White,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                    )
                }

                Text(
                    text = "${result.confidencePercentage}% Match",
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.ExtraBold,
                    color = PrimaryGreen
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = result.diseaseName,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.ExtraBold
            )

            Text(
                text = "Target Animal: ${result.animalType}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 2.dp, bottom = 14.dp)
            )

            HorizontalDivider()
            Spacer(modifier = Modifier.height(14.dp))

            // Immediate Care
            if (result.immediateCare.isNotBlank()) {
                Text(
                    text = "🚨 Immediate Care",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = StatusError
                )
                Text(
                    text = result.immediateCare,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
                )
            }

            // Home Remedies
            if (result.homeRemedies.isNotBlank()) {
                Text(
                    text = "🌿 Home & Traditional Remedies",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = PrimaryGreen
                )
                Text(
                    text = result.homeRemedies,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
                )
            }

            // Veterinary Action
            if (result.veterinaryAction.isNotBlank()) {
                Text(
                    text = "🩺 Veterinary Medical Action",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = StatusInfo
                )
                Text(
                    text = result.veterinaryAction,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 4.dp, bottom = 16.dp)
                )
            }

            // Action Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                OutlinedButton(
                    onClick = onScanAgain,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("New Scan")
                }

                Button(
                    onClick = onAskAI,
                    modifier = Modifier.weight(1.5f),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen)
                ) {
                    Icon(Icons.Filled.SmartToy, contentDescription = "Ask AI")
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Consult AI Vet")
                }
            }
        }
    }
}

private fun copyUriToFile(context: Context, uri: Uri): File? {
    return try {
        val inputStream = context.contentResolver.openInputStream(uri) ?: return null
        val tempFile = File.createTempFile("scan_", ".jpg", context.cacheDir)
        val outputStream = FileOutputStream(tempFile)
        inputStream.copyTo(outputStream)
        inputStream.close()
        outputStream.close()
        tempFile
    } catch (e: Exception) {
        null
    }
}
