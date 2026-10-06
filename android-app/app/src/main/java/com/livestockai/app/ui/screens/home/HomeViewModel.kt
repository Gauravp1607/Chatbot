package com.livestockai.app.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.livestockai.app.data.repository.MarketplaceRepository
import com.livestockai.app.domain.model.Animal
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class HomeUiState(
    val isLoading: Boolean = true,
    val categories: List<String> = emptyList(),
    val featuredAnimals: List<Animal> = emptyList(),
    val recentAnimals: List<Animal> = emptyList(),
    val errorMessage: String? = null
)

class HomeViewModel(private val repository: MarketplaceRepository) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    init {
        loadHomeData()
    }

    fun loadHomeData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)

            val catResult = repository.getCategories()
            val animalsResult = repository.getAnimals(sortBy = "newest")

            val categories = catResult.getOrDefault(listOf("Cow", "Dog", "Cat", "Horse"))
            val animals = animalsResult.getOrDefault(emptyList())

            _uiState.value = HomeUiState(
                isLoading = false,
                categories = categories,
                featuredAnimals = animals.take(4),
                recentAnimals = animals,
                errorMessage = if (animalsResult.isFailure) animalsResult.exceptionOrNull()?.message else null
            )
        }
    }

    fun toggleFavorite(animalId: Int) {
        viewModelScope.launch {
            repository.toggleWishlist(animalId)
            // Update local state
            val updatedRecent = _uiState.value.recentAnimals.map {
                if (it.animalId == animalId) it.copy(isFavorite = !it.isFavorite) else it
            }
            val updatedFeatured = _uiState.value.featuredAnimals.map {
                if (it.animalId == animalId) it.copy(isFavorite = !it.isFavorite) else it
            }
            _uiState.value = _uiState.value.copy(
                recentAnimals = updatedRecent,
                featuredAnimals = updatedFeatured
            )
        }
    }
}
