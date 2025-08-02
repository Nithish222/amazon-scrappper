    def extract_dynamic_data_js(self):
        js_code = textwrap.dedent("""
        () => {
            const data = {};
            try {
                const boughtElement = document.querySelector('#social-proofing-faceout-title-tk_bought');
                data.bought = boughtElement ? boughtElement.textContent.trim() : '';
                console.log("Bought Element:", data.bought);
            } catch (e) { data.bought = ''; }
            try {
                const pricingElement = document.querySelector('#corePriceDisplay_desktop_feature_div');
                if (pricingElement) {
                    const discountElement = pricingElement.querySelector('span.savingPriceOverride');
                    const symbolElement = pricingElement.querySelector('span.a-price-symbol');
                    const wholeElement = pricingElement.querySelector('span.a-price-whole');
                    const mrpElement = pricingElement.querySelector('span.aok-relative span.a-offscreen');
                    data.discount = discountElement ? discountElement.textContent.trim() : '';
                    const symbol = symbolElement ? symbolElement.textContent.trim() : '';
                    const whole = wholeElement ? wholeElement.textContent.trim() : '';
                    data.price = symbol + whole;
                    data.mrp = mrpElement ? mrpElement.textContent.trim() : '';
                } else { data.discount = ''; data.price = ''; data.mrp = ''; }
            } catch (e) { data.discount = ''; data.price = ''; data.mrp = ''; }
            try {
                const offersList = [];
                const offersHolder = document.querySelector('div.a-cardui.vsx__offers-holder');
                if (offersHolder) {
                    const offers = offersHolder.querySelectorAll('li h6.a-size-base.a-spacing-micro.offers-items-title');
                    offers.forEach(offer => {
                        const text = offer.textContent.trim();
                        if (text && !offersList.includes(text)) offersList.push(text);
                    });
                }
                data.offers = offersList;
            } catch (e) { data.offers = []; }
            try {
                const featureList = [];
                const featuresHolder = document.querySelector('div#iconfarmv2_feature_div');
                if (featuresHolder) {
                    const features = featuresHolder.querySelectorAll("li.a-carousel-card:not([aria-hidden='true']) a.a-size-small.a-link-normal.a-text-normal");
                    features.forEach(feature => {
                        const text = feature.textContent.trim();
                        if (text && !featureList.includes(text)) featureList.push(text);
                    });
                }
                data.features = featureList;
            } catch (e) { data.features = []; }
            try {
                const overviewElement = document.querySelector('div#productOverview_feature_div tbody');
                data.overview = overviewElement ? overviewElement.textContent.trim() : '';
            } catch (e) { data.overview = ''; }
            try {
                const frequentlyList = [];
                const freqElement = document.querySelector("div[data-csa-c-content-id='sims-productBundle']");
                if (freqElement) {
                    const productTitles = freqElement.querySelectorAll("span[class='a-size-base']");
                    const productPrices = freqElement.querySelectorAll("span[class='a-price']");
                    for (let i = 0; i < Math.min(productTitles.length, productPrices.length); i++) {
                        const title = productTitles[i].textContent.trim();
                        const priceText = productPrices[i].textContent;
                        const price = priceText ? priceText.trim().replace("\\n", ".") : '';
                        if (title && price) frequentlyList.push({name: title, price: price});
                    }
                }
                data.frequently_bought = frequentlyList;
            } catch (e) { data.frequently_bought = []; }
            try {
                const summaryElement = document.querySelector('div#product-summary p.a-spacing-small');
                data.summary = summaryElement ? summaryElement.textContent.trim() : '';
            } catch (e) { data.summary = ''; }
            try {
                const mentionsList = [];
                const mentionElements = document.querySelectorAll("div[aria-label='Commonly Mentioned Aspects'] a");
                mentionElements.forEach(mention => {
                    const text = mention.textContent.trim();
                    if (text) mentionsList.push(text);
                });
                data.mentions = mentionsList;
            } catch (e) { data.mentions = []; }
            console.log('product_data:', data);
            return data;
        }
        """).strip()
        print(js_code)
        return js_code