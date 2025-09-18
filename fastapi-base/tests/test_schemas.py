from typing import List, Optional

import pytest
from pydantic import BaseModel, ValidationError

from src.schemas.common import IGetResponseBase, IPostResponseBase, IResponseBase


# Sample data models for testing
class User(BaseModel):
    id: int
    name: str
    email: str


class Product(BaseModel):
    id: int
    name: str
    price: float


class TestIResponseBase:
    """Test the base response model"""

    def test_response_base_with_string_data(self):
        """Test IResponseBase with string data"""
        response = IResponseBase[str](
            message="Success", data="Hello World", meta={"version": "1.0"}
        )

        assert response.message == "Success"
        assert response.data == "Hello World"
        assert response.meta == {"version": "1.0"}

    def test_response_base_with_user_model(self):
        """Test IResponseBase with custom model"""
        user = User(id=1, name="John Doe", email="john@example.com")
        response = IResponseBase[User](
            message="User found", data=user, meta={"timestamp": "2023-01-01"}
        )

        assert response.message == "User found"
        assert response.data == user
        assert response.data.name == "John Doe"
        assert response.meta["timestamp"] == "2023-01-01"

    def test_response_base_with_list_data(self):
        """Test IResponseBase with list of models"""
        users = [
            User(id=1, name="John", email="john@example.com"),
            User(id=2, name="Jane", email="jane@example.com"),
        ]
        response = IResponseBase[List[User]](message="Users retrieved", data=users)

        assert response.message == "Users retrieved"
        assert len(response.data) == 2
        assert response.data[0].name == "John"
        assert response.data[1].name == "Jane"

    def test_response_base_defaults(self):
        """Test default values"""
        response = IResponseBase[str]()

        assert response.message == ""
        assert response.meta == {}
        assert response.data is None

    def test_response_base_with_none_data(self):
        """Test with None data"""
        response = IResponseBase[Optional[str]](message="No data found", data=None)

        assert response.message == "No data found"
        assert response.data is None

    def test_response_base_serialization(self):
        """Test JSON serialization"""
        user = User(id=1, name="John", email="john@example.com")
        response = IResponseBase[User](message="Success", data=user, meta={"count": 1})

        json_data = response.model_dump()
        expected = {
            "message": "Success",
            "meta": {"count": 1},
            "data": {"id": 1, "name": "John", "email": "john@example.com"},
        }

        assert json_data == expected


class TestIGetResponseBase:
    """Test the GET response model"""

    def test_get_response_default_message(self):
        """Test default message for GET response"""
        user = User(id=1, name="John", email="john@example.com")
        response = IGetResponseBase[User](data=user)

        assert response.message == "Data fetched correctly"
        assert response.data == user

    def test_get_response_custom_message(self):
        """Test custom message override"""
        response = IGetResponseBase[str](message="Custom fetch message", data="test data")

        assert response.message == "Custom fetch message"
        assert response.data == "test data"

    def test_get_response_with_list(self):
        """Test GET response with list data"""
        products = [
            Product(id=1, name="Laptop", price=999.99),
            Product(id=2, name="Mouse", price=29.99),
        ]
        response = IGetResponseBase[List[Product]](data=products)

        assert response.message == "Data fetched correctly"
        assert len(response.data) == 2
        assert response.data[0].name == "Laptop"

    def test_get_response_empty_data(self):
        """Test GET response with no data"""
        response = IGetResponseBase[Optional[str]](message="No data found")

        assert response.message == "No data found"
        assert response.data is None


class TestIPostResponseBase:
    """Test the POST response model"""

    def test_post_response_default_message(self):
        """Test default message for POST response"""
        user = User(id=1, name="John", email="john@example.com")
        response = IPostResponseBase[User](data=user)

        assert response.message == "Data created correctly"
        assert response.data == user

    def test_post_response_custom_message(self):
        """Test custom message override"""
        response = IPostResponseBase[str](message="Custom creation message", data="created item")

        assert response.message == "Custom creation message"
        assert response.data == "created item"

    def test_post_response_with_meta(self):
        """Test POST response with metadata"""
        user = User(id=1, name="John", email="john@example.com")
        response = IPostResponseBase[User](
            data=user, meta={"created_at": "2023-01-01", "version": "1.0"}
        )

        assert response.message == "Data created correctly"
        assert response.data == user
        assert response.meta["created_at"] == "2023-01-01"


class TestResponseModelsIntegration:
    """Integration tests for response models"""

    def test_different_response_types_same_data(self):
        """Test same data with different response types"""
        user = User(id=1, name="John", email="john@example.com")

        get_response = IGetResponseBase[User](data=user)
        post_response = IPostResponseBase[User](data=user)

        assert get_response.data == post_response.data
        assert get_response.message == "Data fetched correctly"
        assert post_response.message == "Data created correctly"

    def test_nested_generic_types(self):
        """Test with nested generic types"""
        users = [
            User(id=1, name="John", email="john@example.com"),
            User(id=2, name="Jane", email="jane@example.com"),
        ]

        response = IGetResponseBase[List[User]](data=users, meta={"total": 2, "page": 1})

        assert isinstance(response.data, list)
        assert len(response.data) == 2
        assert all(isinstance(user, User) for user in response.data)

    def test_response_inheritance_chain(self):
        """Test that inheritance works correctly"""
        user = User(id=1, name="John", email="john@example.com")

        # IGetResponseBase should inherit from IResponseBase
        get_response = IGetResponseBase[User](data=user)

        # Should have all attributes from base class
        assert hasattr(get_response, "message")
        assert hasattr(get_response, "meta")
        assert hasattr(get_response, "data")

        # Should be instance of both
        assert isinstance(get_response, IGetResponseBase)
        # Note: Due to generics, direct isinstance check with IResponseBase might not work as expected


class TestResponseModelsValidation:
    """Test validation and error cases"""

    def test_invalid_data_type(self):
        """Test that wrong data type raises validation error"""
        with pytest.raises(ValidationError):  # Pydantic validation error
            IResponseBase[int](
                message="Test",
                data="not an integer",  # Wrong type
            )

    def test_meta_must_be_dict(self):
        """Test that meta must be a dictionary"""
        with pytest.raises(ValidationError):  # Pydantic validation error
            IResponseBase[str](
                message="Test",
                meta="not a dict",  # Wrong type
            )

    def test_message_must_be_string(self):
        """Test that message must be a string"""
        with pytest.raises(ValidationError):  # Pydantic validation error
            IResponseBase[str](
                message=123,  # Wrong type
                data="test",
            )


# Additional utility functions for testing
def create_sample_user_response(user_data: dict) -> IGetResponseBase[User]:
    """Helper function to create user responses for testing"""
    user = User(**user_data)
    return IGetResponseBase[User](data=user)


def create_sample_list_response(items: List[dict]) -> IGetResponseBase[List[User]]:
    """Helper function to create list responses for testing"""
    users = [User(**item) for item in items]
    return IGetResponseBase[List[User]](data=users)


# Example usage in actual tests
class TestHelperFunctions:
    """Test the helper functions"""

    def test_create_sample_user_response(self):
        """Test helper function for creating user responses"""
        user_data = {"id": 1, "name": "John", "email": "john@example.com"}
        response = create_sample_user_response(user_data)

        assert response.data.id == 1
        assert response.data.name == "John"
        assert response.message == "Data fetched correctly"

    def test_create_sample_list_response(self):
        """Test helper function for creating list responses"""
        users_data = [
            {"id": 1, "name": "John", "email": "john@example.com"},
            {"id": 2, "name": "Jane", "email": "jane@example.com"},
        ]
        response = create_sample_list_response(users_data)

        assert len(response.data) == 2
        assert response.data[0].name == "John"
        assert response.data[1].name == "Jane"
