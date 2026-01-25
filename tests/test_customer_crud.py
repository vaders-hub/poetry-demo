import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.customer import (
    get_customers,
    get_customer,
    create_customer,
    update_customer,
    delete_customer,
)
from app.models.customer import Customer as CustomerModel


class TestCustomerCRUD:
    """Unit tests for Customer CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_customer_success(self, test_session: AsyncSession):
        """Test successful customer creation."""
        customer_data = CustomerModel(
            customer_id="test-create-id",
            name="Test Create Customer",
            address="123 Create Street",
            website="https://create.test",
            credit_limit=5000
        )

        result = await create_customer(test_session, customer_data)

        assert result.customer_id == "test-create-id"
        assert result.name == "Test Create Customer"
        assert result.address == "123 Create Street"
        assert result.credit_limit == 5000

    @pytest.mark.asyncio
    async def test_create_customer_missing_id(self, test_session: AsyncSession):
        """Test customer creation fails without customer_id."""
        customer_data = CustomerModel(
            customer_id=None,
            name="Test Customer"
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_customer(test_session, customer_data)

        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_create_customer_missing_name(self, test_session: AsyncSession):
        """Test customer creation fails without name."""
        customer_data = CustomerModel(
            customer_id="test-no-name",
            name=None
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_customer(test_session, customer_data)

        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_create_customer_duplicate(self, test_session: AsyncSession):
        """Test creating duplicate customer fails."""
        customer_data = CustomerModel(
            customer_id="duplicate-id",
            name="Duplicate Customer"
        )

        # Create first customer
        await create_customer(test_session, customer_data)

        # Try to create duplicate
        with pytest.raises(HTTPException) as exc_info:
            await create_customer(test_session, customer_data)

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_customers_empty(self, test_session: AsyncSession):
        """Test getting customers when database is empty."""
        with pytest.raises(HTTPException) as exc_info:
            await get_customers(test_session)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_customers_success(self, test_session: AsyncSession):
        """Test successfully getting all customers."""
        # Create test customers
        customer1 = CustomerModel(customer_id="id1", name="Customer 1")
        customer2 = CustomerModel(customer_id="id2", name="Customer 2")

        await create_customer(test_session, customer1)
        await create_customer(test_session, customer2)

        # Get all customers
        customers = await get_customers(test_session)

        assert len(customers) == 2
        assert customers[0].name in ["Customer 1", "Customer 2"]
        assert customers[1].name in ["Customer 1", "Customer 2"]

    @pytest.mark.asyncio
    async def test_get_customer_by_id_success(self, test_session: AsyncSession):
        """Test successfully getting a customer by ID."""
        customer_data = CustomerModel(
            customer_id="get-by-id-test",
            name="Get By ID Customer"
        )
        await create_customer(test_session, customer_data)

        # Get customer by ID
        customer = await get_customer(test_session, "get-by-id-test")

        assert customer.customer_id == "get-by-id-test"
        assert customer.name == "Get By ID Customer"

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, test_session: AsyncSession):
        """Test getting non-existent customer raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            await get_customer(test_session, "non-existent-id")

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_customer_success(self, test_session: AsyncSession):
        """Test successfully updating a customer."""
        # Create customer
        customer_data = CustomerModel(
            customer_id="update-test-id",
            name="Original Name",
            address="Original Address",
            credit_limit=1000
        )
        await create_customer(test_session, customer_data)

        # Update customer
        updated_data = CustomerModel(
            customer_id="update-test-id",
            name="Updated Name",
            address="Updated Address",
            credit_limit=2000
        )
        result = await update_customer(test_session, updated_data)

        assert result.customer_id == "update-test-id"
        assert result.name == "Updated Name"
        assert result.address == "Updated Address"
        assert result.credit_limit == 2000

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, test_session: AsyncSession):
        """Test updating non-existent customer fails."""
        customer_data = CustomerModel(
            customer_id="non-existent-update",
            name="Test"
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_customer(test_session, customer_data)

        assert exc_info.value.status_code == 404
        assert "does not exist" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_delete_customer_success(self, test_session: AsyncSession):
        """Test successfully deleting a customer."""
        # Create customer
        customer_data = CustomerModel(
            customer_id="delete-test-id",
            name="To Be Deleted"
        )
        await create_customer(test_session, customer_data)

        # Delete customer
        result = await delete_customer(test_session, customer_data)

        assert result.customer_id == "delete-test-id"

        # Verify deletion
        with pytest.raises(HTTPException) as exc_info:
            await get_customer(test_session, "delete-test-id")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, test_session: AsyncSession):
        """Test deleting non-existent customer fails."""
        customer_data = CustomerModel(
            customer_id="non-existent-delete",
            name="Test"
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_customer(test_session, customer_data)

        assert exc_info.value.status_code == 404
        assert "does not exist" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_crud_workflow(self, test_session: AsyncSession):
        """Test complete CRUD workflow."""
        customer_id = "workflow-crud-test"

        # 1. Create
        create_data = CustomerModel(
            customer_id=customer_id,
            name="Workflow Customer",
            address="Workflow Address",
            credit_limit=3000
        )
        created = await create_customer(test_session, create_data)
        assert created.name == "Workflow Customer"

        # 2. Read
        fetched = await get_customer(test_session, customer_id)
        assert fetched.customer_id == customer_id
        assert fetched.name == "Workflow Customer"

        # 3. Update
        update_data = CustomerModel(
            customer_id=customer_id,
            name="Updated Workflow",
            address="New Address",
            credit_limit=5000
        )
        updated = await update_customer(test_session, update_data)
        assert updated.name == "Updated Workflow"
        assert updated.credit_limit == 5000

        # 4. Delete
        await delete_customer(test_session, update_data)

        # 5. Verify deletion
        with pytest.raises(HTTPException):
            await get_customer(test_session, customer_id)
