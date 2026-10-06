package com.livestockai.app.ui.screens.scanner

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.livestockai.app.data.repository.AIRepository
import com.livestockai.app.domain.model.DiagnosisResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File

sealed class ScannerState {
    object Idle : ScannerState()
    data class ImageSelected(val imageUri: Uri, val imageFile: File) : ScannerState()
    object Scanning : ScannerState()
    data class Success(val result: DiagnosisResult) : ScannerState()
    data class Error(val message: String) : ScannerState()
}

class DiseaseScannerViewModel(private val aiRepository: AIRepository) : ViewModel() {

    private val _scannerState = MutableStateFlow<ScannerState>(ScannerState.Idle)
    val scannerState: StateFlow<ScannerState> = _scannerState.asStateFlow()

    fun onImageSelected(uri: Uri, file: File) {
        _scannerState.value = ScannerState.ImageSelected(uri, file)
    }

    fun startScan() {
        val currentState = _scannerState.value
        if (currentState is ScannerState.ImageSelected) {
            viewModelScope.launch {
                _scannerState.value = ScannerState.Scanning
                val result = aiRepository.detectDisease(currentState.imageFile)
                result.onSuccess { diag ->
                    _scannerState.value = ScannerState.Success(diag)
                }.onFailure { error ->
                    _scannerState.value = ScannerState.Error(error.message ?: "Diagnosis scan failed.")
                }
            }
        }
    }

    fun reset() {
        _scannerState.value = ScannerState.Idle
    }
}
