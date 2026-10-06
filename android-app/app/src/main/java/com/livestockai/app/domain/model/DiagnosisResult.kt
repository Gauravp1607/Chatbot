package com.livestockai.app.domain.model

data class DiagnosisResult(
    val diseaseName: String,
    val confidence: Double,
    val severity: String = "Medium",
    val animalType: String = "Livestock",
    val symptoms: List<String> = emptyList(),
    val immediateCare: String = "",
    val homeRemedies: String = "",
    val veterinaryAction: String = "",
    val imageUrl: String? = null
) {
    val confidencePercentage: Int get() = (confidence * 100).toInt()
}
