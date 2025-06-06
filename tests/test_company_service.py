"""Tests for company service functions."""

import pytest
from decimal import Decimal

from app.services.company_service import validate_nip, create_company_profile, get_company_profile
from app.models.company_models import CompanyProfile


class TestNIPValidation:
    """Test NIP validation function."""
    
    def test_valid_nip(self):
        """Test valid NIP numbers."""
        # Let's calculate a proper valid NIP: 123-456-32-X
        # Weights: [6, 5, 7, 2, 3, 4, 5, 6, 7]
        # Digits: [1, 2, 3, 4, 5, 6, 3, 2, X] (X is checksum)
        # Sum: 1*6 + 2*5 + 3*7 + 4*2 + 5*3 + 6*4 + 3*5 + 2*6 = 6+10+21+8+15+24+15+12 = 111
        # 111 % 11 = 1, but let me recalculate: 1*6 + 2*5 + 3*7 + 4*2 + 5*3 + 6*4 + 3*5 + 2*6 + 2*7 = 125
        # 125 % 11 = 4, so checksum should be 4
        test_nip = "1234563224"
        assert validate_nip(test_nip), f"NIP {test_nip} should be valid"

        # Test another valid NIP: 526-000-12-X
        # Sum: 5*6 + 2*5 + 6*7 + 0*2 + 0*3 + 0*4 + 1*5 + 2*6 + 2*7 = 30+10+42+0+0+0+5+12+14 = 113
        # 113 % 11 = 3, so checksum should be 3
        test_nip2 = "5260001223"
        assert validate_nip(test_nip2), f"NIP {test_nip2} should be valid"
    
    def test_invalid_nip_wrong_length(self):
        """Test NIP with wrong length."""
        invalid_nips = [
            "123456321",   # Too short
            "12345632189", # Too long
            "",            # Empty
            "123",         # Way too short
        ]
        
        for nip in invalid_nips:
            assert not validate_nip(nip), f"NIP {nip} should be invalid"
    
    def test_invalid_nip_wrong_checksum(self):
        """Test NIP with wrong checksum."""
        invalid_nips = [
            "1234563219",  # Wrong checksum
            "5260001247",  # Wrong checksum
        ]
        
        for nip in invalid_nips:
            assert not validate_nip(nip), f"NIP {nip} should be invalid"
    
    def test_nip_with_formatting(self):
        """Test NIP with formatting characters."""
        # Should handle formatting
        assert validate_nip("123-456-32-18")
        assert validate_nip("123 456 32 18")
        assert validate_nip("123.456.32.18")


class TestCompanyService:
    """Test company service functions."""
    
    @pytest.mark.asyncio
    async def test_create_company_profile(self, test_session):
        """Test creating a company profile."""
        profile_data = {
            "name": "Test Company Sp. z o.o.",
            "nip": "1234563224",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001",
            "email": "test@company.pl"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        assert company_profile.id is not None
        assert company_profile.name == "Test Company Sp. z o.o."
        assert company_profile.nip == "1234563224"
        assert company_profile.city == "Warszawa"
    
    @pytest.mark.asyncio
    async def test_create_company_profile_invalid_nip(self, test_session):
        """Test creating company profile with invalid NIP."""
        profile_data = {
            "name": "Test Company",
            "nip": "1234567890",  # Invalid NIP
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        with pytest.raises(ValueError, match="Invalid NIP number"):
            await create_company_profile(test_session, profile_data)
    
    @pytest.mark.asyncio
    async def test_create_duplicate_company_profile(self, test_session):
        """Test creating duplicate company profile."""
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        # Create first profile
        await create_company_profile(test_session, profile_data)
        
        # Try to create second profile
        with pytest.raises(ValueError, match="Company profile already exists"):
            await create_company_profile(test_session, profile_data)
    
    @pytest.mark.asyncio
    async def test_get_company_profile_empty(self, test_session):
        """Test getting company profile when none exists."""
        profile = await get_company_profile(test_session)
        assert profile is None
    
    @pytest.mark.asyncio
    async def test_get_company_profile_exists(self, test_session):
        """Test getting existing company profile."""
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        created_profile = await create_company_profile(test_session, profile_data)
        retrieved_profile = await get_company_profile(test_session)
        
        assert retrieved_profile is not None
        assert retrieved_profile.id == created_profile.id
        assert retrieved_profile.name == "Test Company"
