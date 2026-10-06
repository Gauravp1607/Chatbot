package com.livestockai.app.ui.screens.sell

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.livestockai.app.data.repository.MarketplaceRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import java.io.FileOutputStream

sealed class AddListingState {
    object Idle : AddListingState()
    object Loading : AddListingState()
    object Success : AddListingState()
    data class Error(val message: String) : AddListingState()
}

class AddListingViewModel(private val repository: MarketplaceRepository) : ViewModel() {

    private val _state = MutableStateFlow<AddListingState>(AddListingState.Idle)
    val state: StateFlow<AddListingState> = _state.asStateFlow()

    fun submitListing(
        animalType: String,
        breed: String,
        animalName: String,
        age: String,
        weight: String,
        gender: String,
        price: String,
        city: String,
        state: String,
        milkYield: String,
        vaccinated: Boolean,
        healthStatus: String,
        description: String,
        imageFile: File?
    ) {
        if (animalType.isBlank() || breed.isBlank() || price.isBlank()) {
            _state.value = AddListingState.Error("Animal Type, Breed, and Price are required.")
            return
        }

        viewModelScope.launch {
            _state.value = AddListingState.Loading
            val result = repository.createAnimalListing(
                animalType = animalType.trim(),
                breed = breed.trim(),
                animalName = animalName.trim().ifBlank { "$animalType $breed" },
                age = age.toIntOrNull() ?: 12,
                weight = weight.toDoubleOrNull() ?: 100.0,
                gender = gender,
                price = price.toDoubleOrNull() ?: 0.0,
                city = city.trim(),
                state = state.trim(),
                milkYield = milkYield.toDoubleOrNull() ?: 0.0,
                vaccinated = vaccinated,
                healthStatus = healthStatus,
                description = description.trim(),
                imageFile = imageFile
            )

            result.onSuccess {
                _state.value = AddListingState.Success
            }.onFailure { error ->
                _state.value = AddListingState.Error(error.message ?: "Failed to list animal.")
            }
        }
    }

    fun resetState() {
        _state.value = AddListingState.Idle
    }
}
