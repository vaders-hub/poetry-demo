import pytest
from httpx import AsyncClient


class TestCustomerRoutes:
    """Test cases for Customer API routes."""

    @pytest.mark.asyncio
    async def test_create_customer(self, client: AsyncClient, sample_customer_data):
        """Test creating a new customer."""
        response = await client.post("/customer/add", json=sample_customer_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "customer created"
        assert data["data"]["name"] == sample_customer_data["name"]
        assert data["data"]["customer_id"] == sample_customer_data["customer_id"]

    @pytest.mark.asyncio
    async def test_create_customer_duplicate(self, client: AsyncClient, sample_customer_data):
        """Test creating a duplicate customer should fail."""
        # Create first customer
        await client.post("/customer/add", json=sample_customer_data)

        # Try to create duplicate
        response = await client.post("/customer/add", json=sample_customer_data)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_customer_missing_name(self, client: AsyncClient):
        """Test creating a customer without name should fail."""
        customer_data = {
            "customer_id": "test-uuid-missing-name",
            "address": "123 Test Street"
        }

        response = await client.post("/customer/add", json=customer_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_customer_list_empty(self, client: AsyncClient):
        """Test getting customer list when empty."""
        response = await client.get("/customer/list")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_customer_list(self, client: AsyncClient, sample_customer_data):
        """Test getting customer list."""
        # Create a customer first
        await client.post("/customer/add", json=sample_customer_data)

        response = await client.get("/customer/list")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == sample_customer_data["name"]

    @pytest.mark.asyncio
    async def test_get_customer_by_id(self, client: AsyncClient, sample_customer_data):
        """Test getting a specific customer by ID."""
        # Create a customer first
        await client.post("/customer/add", json=sample_customer_data)

        customer_id = sample_customer_data["customer_id"]
        response = await client.get(f"/customer/{customer_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["customer_id"] == customer_id
        assert data["data"]["name"] == sample_customer_data["name"]

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, client: AsyncClient):
        """Test getting a non-existent customer."""
        response = await client.get("/customer/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_customer(self, client: AsyncClient, sample_customer_data):
        """Test updating a customer."""
        # Create a customer first
        await client.post("/customer/add", json=sample_customer_data)

        # Update the customer
        updated_data = sample_customer_data.copy()
        updated_data["name"] = "Updated Customer Name"
        updated_data["credit_limit"] = 20000

        response = await client.put("/customer/modify", json=updated_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Customer Name"
        assert data["data"]["credit_limit"] == 20000

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, client: AsyncClient):
        """Test updating a non-existent customer."""
        customer_data = {
            "customer_id": "non-existent-id",
            "name": "Test Name"
        }

        response = await client.put("/customer/modify", json=customer_data)

        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_customer(self, client: AsyncClient, sample_customer_data):
        """Test deleting a customer."""
        # Create a customer first
        await client.post("/customer/add", json=sample_customer_data)

        # Delete the customer
        response = await client.delete("/customer/delete", json=sample_customer_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "customer deleted"

        # Verify customer is deleted
        get_response = await client.get(f"/customer/{sample_customer_data['customer_id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, client: AsyncClient):
        """Test deleting a non-existent customer."""
        customer_data = {
            "customer_id": "non-existent-id",
            "name": "Test"
        }

        response = await client.delete("/customer/delete", json=customer_data)

        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_customer_crud_workflow(self, client: AsyncClient):
        """Test complete CRUD workflow for customer."""
        # 1. Create
        customer_data = {
            "customer_id": "workflow-test-id",
            "name": "Workflow Test Customer",
            "address": "456 Workflow Street",
            "website": "https://workflow.test",
            "credit_limit": 15000
        }

        create_response = await client.post("/customer/add", json=customer_data)
        assert create_response.status_code == 200

        # 2. Read
        read_response = await client.get(f"/customer/{customer_data['customer_id']}")
        assert read_response.status_code == 200
        assert read_response.json()["data"]["name"] == customer_data["name"]

        # 3. Update
        customer_data["name"] = "Updated Workflow Customer"
        update_response = await client.put("/customer/modify", json=customer_data)
        assert update_response.status_code == 200
        assert update_response.json()["data"]["name"] == "Updated Workflow Customer"

        # 4. Delete
        delete_response = await client.delete("/customer/delete", json=customer_data)
        assert delete_response.status_code == 200

        # 5. Verify deletion
        verify_response = await client.get(f"/customer/{customer_data['customer_id']}")
        assert verify_response.status_code == 404
