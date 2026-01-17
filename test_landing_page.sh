#!/bin/bash
# Landing Page Testing Script

echo "🧪 Testing CryptoVault Landing Page Improvements"
echo "================================================"
echo ""

# Test 1: Check homepage loads
echo "1️⃣ Testing Homepage Load..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$RESPONSE" = "200" ]; then
    echo "   ✅ Homepage loads successfully (200 OK)"
else
    echo "   ❌ Homepage failed to load (Status: $RESPONSE)"
fi
echo ""

# Test 2: Check new headline
echo "2️⃣ Testing New Headline..."
HEADLINE=$(curl -s http://localhost:3000 | grep -o "The Custody Solution")
if [ ! -z "$HEADLINE" ]; then
    echo "   ✅ New headline detected: 'The Custody Solution Institutions Trust...'"
else
    echo "   ⚠️  Could not verify headline (page may still be loading)"
fi
echo ""

# Test 3: Check schema markup
echo "3️⃣ Testing Schema Markup..."
SCHEMA_COUNT=$(curl -s http://localhost:3000 | grep -o 'application/ld+json' | wc -l)
if [ "$SCHEMA_COUNT" -gt 0 ]; then
    echo "   ✅ Schema markup detected ($SCHEMA_COUNT schemas found)"
    echo "   📋 Expected schemas: Organization, Service, FAQ, Breadcrumb"
else
    echo "   ❌ No schema markup found"
fi
echo ""

# Test 4: Check meta tags
echo "4️⃣ Testing Enhanced Meta Tags..."
META_TITLE=$(curl -s http://localhost:3000 | grep -o "<title>.*CryptoVault.*</title>")
if [ ! -z "$META_TITLE" ]; then
    echo "   ✅ Meta title found"
fi

OG_TAGS=$(curl -s http://localhost:3000 | grep -c 'property="og:')
if [ "$OG_TAGS" -gt 0 ]; then
    echo "   ✅ Open Graph tags found ($OG_TAGS tags)"
fi

TWITTER_TAGS=$(curl -s http://localhost:3000 | grep -c 'name="twitter:')
if [ "$TWITTER_TAGS" -gt 0 ]; then
    echo "   ✅ Twitter Card tags found ($TWITTER_TAGS tags)"
fi
echo ""

# Test 5: Check for FAQ section
echo "5️⃣ Testing FAQ Section..."
FAQ_SECTION=$(curl -s http://localhost:3000 | grep -c 'Frequently Asked')
if [ "$FAQ_SECTION" -gt 0 ]; then
    echo "   ✅ FAQ section detected on page"
else
    echo "   ⚠️  FAQ section not found in HTML"
fi
echo ""

# Test 6: Backend health check
echo "6️⃣ Testing Backend Connection..."
BACKEND_HEALTH=$(curl -s http://localhost:8001/health 2>/dev/null)
if [ ! -z "$BACKEND_HEALTH" ]; then
    echo "   ✅ Backend API responding"
else
    echo "   ❌ Backend not responding"
fi
echo ""

echo "================================================"
echo "✨ Testing Complete!"
echo ""
echo "📊 Manual Testing Checklist:"
echo "   1. Visit http://localhost:3000"
echo "   2. Verify new headline: 'The Custody Solution Institutions Trust With \$10B+'"
echo "   3. Check testimonials have photos and verified badges"
echo "   4. Scroll to FAQ section and test accordion"
echo "   5. Verify CTA section shows certifications (not media logos)"
echo "   6. Check trust indicators show: Zero Breaches, \$10.2B, 5 Jurisdictions"
echo ""
echo "🔍 SEO Validation:"
echo "   • Rich Results Test: https://search.google.com/test/rich-results"
echo "   • Schema Validator: https://validator.schema.org"
echo "   • Meta Tags Preview: https://metatags.io"
echo ""
