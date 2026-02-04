"""
Fraud Detection Service
Stealth collection and analysis of device/IP data for fraud prevention
"""
import logging
import hashlib
from typing import Dict, Any, Optional
from fastapi import Request

logger = logging.getLogger(__name__)


class FraudDetectionService:
    """Fraud detection using IP analysis and device fingerprinting"""
    
    # Known proxy headers
    PROXY_HEADERS = [
        'via',
        'x-forwarded-for',
        'x-proxy-id',
        'proxy-connection',
        'forwarded',
        'x-real-ip',
        'client-ip'
    ]
    
    # Known VPN/Proxy indicators
    PROXY_KEYWORDS = [
        'proxy',
        'vpn',
        'anonymous',
        'tor',
        'cloudflare',
        'fastly'
    ]
    
    @staticmethod
    def extract_real_ip(request: Request) -> str:
        """Extract real IP address from request headers"""
        
        # Check Cloudflare header (if behind CF)
        cf_ip = request.headers.get('cf-connecting-ip')
        if cf_ip:
            logger.debug(f"Real IP from Cloudflare: {cf_ip}")
            return cf_ip
        
        # Check X-Forwarded-For (common reverse proxy header)
        forwarded = request.headers.get('x-forwarded-for')
        if forwarded:
            # Take first IP (original client)
            ip = forwarded.split(',')[0].strip()
            logger.debug(f"Real IP from X-Forwarded-For: {ip}")
            return ip
        
        # Check X-Real-IP
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            logger.debug(f"Real IP from X-Real-IP: {real_ip}")
            return real_ip
        
        # Fallback to direct connection IP
        direct_ip = request.client.host if request.client else 'unknown'
        logger.debug(f"Direct connection IP: {direct_ip}")
        return direct_ip
    
    @classmethod
    def detect_proxy(cls, request: Request) -> bool:
        """Detect if request is coming through proxy/VPN"""
        
        # Check for proxy headers
        headers_lower = {k.lower(): v for k, v in request.headers.items()}
        
        for proxy_header in cls.PROXY_HEADERS:
            if proxy_header in headers_lower:
                value = headers_lower[proxy_header].lower()
                logger.warning(f"Proxy indicator found: {proxy_header} = {value}")
                return True
        
        # Check user-agent for proxy keywords
        user_agent = request.headers.get('user-agent', '').lower()
        for keyword in cls.PROXY_KEYWORDS:
            if keyword in user_agent:
                logger.warning(f"Proxy keyword in user-agent: {keyword}")
                return True
        
        # Check if X-Forwarded-For has multiple IPs (chain of proxies)
        forwarded = request.headers.get('x-forwarded-for')
        if forwarded and len(forwarded.split(',')) > 2:
            logger.warning(f"Multiple proxy chain detected: {forwarded}")
            return True
        
        return False
    
    @staticmethod
    def hash_fingerprint(fingerprint: str) -> str:
        """Hash device fingerprint for privacy (GDPR compliance)"""
        if not fingerprint:
            return ''
        
        # SHA256 hash for anonymization
        return hashlib.sha256(fingerprint.encode()).hexdigest()
    
    @classmethod
    def collect_fraud_data(cls, request: Request, fingerprint_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Collect all fraud detection data from request"""
        
        real_ip = cls.extract_real_ip(request)
        is_proxied = cls.detect_proxy(request)
        user_agent = request.headers.get('user-agent', 'Unknown')
        
        fraud_data = {
            'ip_address': real_ip,
            'is_proxied': is_proxied,
            'user_agent': user_agent,
            'accept_language': request.headers.get('accept-language', 'Unknown'),
            'accept_encoding': request.headers.get('accept-encoding', 'Unknown'),
        }
        
        # Add fingerprint data if provided (from frontend JS)
        if fingerprint_data:
            fraud_data['device_fingerprint'] = cls.hash_fingerprint(fingerprint_data.get('fingerprint', ''))
            fraud_data['device_fingerprint_raw'] = fingerprint_data.get('fingerprint', '')  # Store raw for admin
            fraud_data['screen_info'] = fingerprint_data.get('screen_info', {})
        
        # Risk scoring (0-100, higher = more suspicious)
        risk_score = 0
        if is_proxied:
            risk_score += 50
        if 'unknown' in user_agent.lower():
            risk_score += 20
        if not fingerprint_data:
            risk_score += 10
        
        fraud_data['risk_score'] = min(risk_score, 100)
        fraud_data['risk_level'] = 'high' if risk_score > 70 else 'medium' if risk_score > 40 else 'low'
        
        return fraud_data
    
    @staticmethod
    def get_device_info(user_agent: str) -> Dict[str, str]:
        """Parse user agent to extract device info"""
        
        ua_lower = user_agent.lower()
        
        # Detect OS
        if 'windows' in ua_lower:
            os = 'Windows'
        elif 'mac' in ua_lower:
            os = 'macOS'
        elif 'linux' in ua_lower:
            os = 'Linux'
        elif 'android' in ua_lower:
            os = 'Android'
        elif 'iphone' in ua_lower or 'ipad' in ua_lower:
            os = 'iOS'
        else:
            os = 'Unknown'
        
        # Detect browser
        if 'edg/' in ua_lower:
            browser = 'Edge'
        elif 'chrome' in ua_lower:
            browser = 'Chrome'
        elif 'firefox' in ua_lower:
            browser = 'Firefox'
        elif 'safari' in ua_lower:
            browser = 'Safari'
        elif 'opera' in ua_lower:
            browser = 'Opera'
        else:
            browser = 'Unknown'
        
        # Detect device type
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            device_type = 'Mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            device_type = 'Tablet'
        else:
            device_type = 'Desktop'
        
        return {
            'os': os,
            'browser': browser,
            'device_type': device_type
        }


# Global service instance
fraud_detection = FraudDetectionService()
