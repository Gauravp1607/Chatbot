package com.livestockai.app.domain.model

data class Order(
    val orderId: Int,
    val animalId: Int,
    val animalName: String,
    val animalType: String,
    val breed: String,
    val price: Double,
    val buyerPayableAmount: Double? = null,
    val orderStatus: String = "Pending",
    val paymentStatus: String = "Pending",
    val imageUrl: String? = null,
    val sellerName: String? = null,
    val buyerName: String? = null,
    val createdAt: String? = null
) {
    val formattedPrice: String get() = "₹%,.0f".format(buyerPayableAmount ?: price)
}
