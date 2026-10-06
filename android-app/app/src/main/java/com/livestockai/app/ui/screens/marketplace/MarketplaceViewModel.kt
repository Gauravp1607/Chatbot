package com.livestockai.app.ui.screens.marketplace

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.livestockai.app.data.repository.MarketplaceRepository
import com.livestockai.app.domain.model.Animal
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class MarketplaceUiState(
    val isLoading: Boolean = false,
    val animals: List<Animal> = emptyList(),
    val categories: List<String> = emptyList(),
    val selectedCategory: String? = null,
    val searchQuery: String = "",
    val minPrice: Double? = null,
    val maxPrice: Double? = null,
    val vaccinatedOnly: Boolean = false,
    val sortBy: String = "newest",
    val errorMessage: String? = null
)

class MarketplaceViewModel(private val repository: MarketplaceRepository) : ViewModel() {

    private val _uiState = MutableStateFlow(MarketplaceUiState())
    val uiState: StateFlow<MarketplaceUiState> = _uiState.asStateFlow()

    private var searchJob: Job? = null

    init {
        loadCategories()
        fetchAnimals()
    }

    private fun loadCategories() {
        viewModelScope.launch {
            val result = repository.getCategories()
            if (result.isSuccess) {
                _uiState.value = _uiState.value.copy(categories = result.getOrDefault(emptyList()))
            }
        }
    }

    fun onSearchQueryChanged(query: String) {
        _uiState.value = _uiState.value.copy(searchQuery = query)
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(400) // Debounce search
            fetchAnimals()
        }
    }

    fun onCategorySelected(category: String?) {
        val newCategory = if (_uiState.value.selectedCategory == category) null else category
        _uiState.value = _uiState.value.copy(selectedCategory = newCategory)
        fetchAnimals()
    }

    fun applyFilters(minPrice: Double?, maxPrice: Double?, vaccinatedOnly: Boolean, sortBy: String) {
        _uiState.value = _uiState.value.copy(
            minPrice = minPrice,
            maxPrice = maxPrice,
            vaccinatedOnly = vaccinatedOnly,
            sortBy = sortBy
        )
        fetchAnimals()
    }

    fun fetchAnimals() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)
            val currentState = _uiState.value
            val result = repository.getAnimals(
                query = currentState.searchQuery.ifBlank { null },
                type = currentState.selectedCategory,
                vaccinated = if (currentState.vaccinatedOnly) "1" else null,
                minPrice = currentState.minPrice,
                maxPrice = currentState.maxPrice,
                sortBy = currentState.sortBy
            )
            result.onSuccess { animals ->
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    animals = animals
                )
            }.onFailure { error ->
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = error.message ?: "Failed to fetch listings"
                )
            }
        }
    }

    fun toggleFavorite(animalId: Int) {
        viewModelScope.launch {
            repository.toggleWishlist(animalId)
            val updated = _uiState.value.animals.map {
                if (it.animalId == animalId) it.copy(isFavorite = !it.isFavorite) else it
            }
            _uiState.value = _uiState.value.copy(animals = updated)
        }
    }
}
