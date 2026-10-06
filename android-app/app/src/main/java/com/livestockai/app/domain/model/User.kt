package com.livestockai.app.domain.model

data class User(
    val userId: Int,
    val fullName: String,
    val email: String,
    val phone: String? = null,
    val role: String = "Buyer",
    val profileImage: String? = null,
    val address: String? = null,
    val city: String? = null,
    val state: String? = null,
    val sellerId: Int? = null,
    val buyerId: Int? = null
) {
    val isSeller: Boolean get() = role.equals("Seller", ignoreCase = true) || role.equals("Admin", ignoreCase = true)
    val isAdmin: Boolean get() = role.equals("Admin", ignoreCase = true)
}
