import json
import requests
from datetime import date
import pandas as pd


from define_collection_wave import folder
from helpers import create_folder, clean_text

file_burgerking_csv = create_folder('12_BurgerKing', folder)
file_burgerking_json = file_burgerking_csv + '/burgerking_nutrition.json'
file_burgerking_csv = file_burgerking_csv + '/burgerking_nutrition.csv'


def crawl_burgerking_nutrition():
    """Crawl Burger King nutrition data using GraphQL API"""
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://www.burgerking.co.uk',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 Edg/130.0.0.0',
    }

    params = {
        'operationName': 'GetStaticPage',
    }

    json_data = {
        'operationName': 'GetStaticPage',
        'variables': '{"id":"a180e7eb-948b-44d0-adca-187b413b14f1"}',
        'query': 'query GetStaticPage($id:ID!){StaticPage(id:$id){_id path{_key _type current __typename}title localeTitle{locale:en __typename}metaTags{title{locale:en __typename}description{locale:en __typename}__typename}ogTags{title{locale:en __typename}description{locale:en __typename}url{locale:en __typename}imageUrl{locale:en __typename}__typename}widgets{...NutritionExplorerWidgetFragment ...on YoutubeWidget{_key _type videoId videoAutoplay __typename}...on HeaderWidget{_key _type headingContent{locale:en __typename}taglineContent{locale:en __typename}headerImage{locale:en{...ImageFragment __typename}__typename}__typename}...on VideoWidget{_key _type video{locale:en{...VideoFileFragment __typename}__typename}caption{locale:en __typename}attributionLink __typename}...on AccordionWidget{_key _type accordionTitle{locale:en __typename}accordionContent{collapsedContent{locale:en __typename}expandedContent{locale:en __typename}__typename}__typename}...on LocaleBlockTextWidget{_key _type blockTextInversion localeBlockTextContent{localeRaw:enRaw __typename}__typename}...on PreviewWidget{_key _type previewContent{previewImage{locale:en{...ImageFragment __typename}__typename}titleText{locale:en __typename}bodyText{locale:en __typename}linkText{locale:en __typename}linkURL localizedLinkURL{locale:en __typename}__typename}__typename}...on ImageWidget{_key _type caption{locale:en __typename}attributionLink image{locale:en{...ImageFragment __typename}__typename}__typename}...on CallToActionWidget{_key _type callToActionContent{heading{locale:en __typename}subheading{locale:en __typename}body{locale:en __typename}buttonText{locale:en __typename}buttonLink link{locale:en __typename}image{locale:en{...ImageFragment __typename}__typename}__typename}__typename}...on QuoteWidget{_key _type quoteText{locale:en __typename}attributionImage{...ImageFragment __typename}attributionName attributionTitle{locale:en __typename}__typename}...on NutritionInfoWidget{_key _type nutritionalSection{name{locale:en __typename}products{...ItemFragment ...on NutritionalSection{name{locale:en __typename}products{...ItemFragment __typename}__typename}__typename}__typename}__typename}...on MultiWidget{_key _type widget __typename}...on DoubleImageWidget{_key _type image1{caption{locale:en __typename}attributionLink image{locale:en{...ImageFragment __typename}__typename}__typename}image2{caption{locale:en __typename}attributionLink image{locale:en{...ImageFragment __typename}__typename}__typename}__typename}...on AnchorWidget{_key _type anchorName{locale:en __typename}__typename}...on RewardsCarouselWidget{_key _type rewardsCarouselTitle{locale:en __typename}rewardsCarouselDescription{locale:en __typename}rewardCarouselCategories{_id label{locale:en __typename}rewards{_id name{locale:en __typename}image{locale:en{...ImageFragment __typename}__typename}__typename}__typename}__typename}...on AnchorLinksWidget{_key _type title{locale:en __typename}__typename}...on DownloadFileWidget{_key _type url{locale:en __typename}__typename}...on LoyaltyBannerWidget{_key _type enabled unauthenticatedDesktopBackgroundImage{locale:en{...ImageFragment __typename}__typename}unauthenticatedMobileBackgroundImage{locale:en{...ImageFragment __typename}__typename}__typename}...on LoyaltyTabSelectorWidget{_key _type tabs{_type link title __typename}__typename}...on InfoCellsWidget{_key _type title{locale:en __typename}icon{locale:en{...ImageFragment __typename}__typename}infoCells{loyaltyTiersSignupCellTitle{locale:en __typename}loyaltyTiersSignupCellDescription{locale:en __typename}loyaltyTiersSignupCellImage{locale:en{...ImageFragment __typename}__typename}__typename}__typename}__typename}pageCSS{code __typename}pageHtml{code __typename}__typename}}fragment NutritionExplorerWidgetFragment on NutritionExplorerWidget{_key _type menu{...NutritionExplorerMenuFragment __typename}viewMenuButtonText{locale:en __typename}moreOptionsButtonText{locale:en __typename}madLibFilterGroup{...FilterGroupFragment __typename}modalFilterGroups{...FilterGroupFragment __typename}categoryWhitelist{...on Section{_id _type __typename}...on Picker{_id _type __typename}__typename}__typename}fragment NutritionExplorerMenuFragment on Menu{_id _type options{...NutritionExplorerPickerFragment ...NutritionExplorerSectionFragment ...NutritionExplorerItemFragment ...NutritionExplorerComboFragment __typename}pickerBackgroundImage{...ImageFragment __typename}__typename}fragment NutritionExplorerPickerFragment on Picker{_id _type name{locale:en __typename}image{...ImageFragment __typename}pickerDefaults{pickerAspect{_id __typename}pickerAspectValueIdentifier __typename}pickerAspects{_id _type pickerAspectOptions{identifier __typename}__typename}pickerAspectItemOptionMappings{pickerAspect{_id __typename}options{value __typename}__typename}options{pickerItemMappings{pickerAspectValueIdentifier pickerAspect{_id __typename}__typename}option{...NutritionExplorerItemFragment ...NutritionExplorerComboFragment __typename}__typename}__typename}fragment ImageFragment on Image{hotspot{x y height width __typename}crop{top bottom left right __typename}asset{metadata{lqip __typename}_id __typename}__typename}fragment NutritionExplorerItemFragment on Item{_id _type name{locale:en __typename}image{...ImageFragment __typename}options{options{default nutrition{...NutritionFragment __typename}__typename}__typename}nutrition{...NutritionFragment __typename}productSize additionalItemInformation{ingredients{locale:en __typename}additives{locale:en __typename}producerDetails{locale:en __typename}__typename}nutritionWithModifiers{...NutritionFragment __typename}allergens{milk eggs fish peanuts shellfish treeNuts soy wheat mustard sesame celery lupin gluten sulphurDioxide __typename}__typename}fragment NutritionFragment on Nutrition{calories caloriesPer100 carbohydrates carbohydratesPer100 cholesterol energyKJ energyKJPer100 fat fatPer100 fiber proteins proteinsPer100 salt saltPer100 saturatedFat saturatedFatPer100 sodium sugar sugarPer100 transFat weight __typename}fragment NutritionExplorerComboFragment on Combo{_id _type name{locale:en __typename}image{...ImageFragment __typename}mainItem{...NutritionExplorerItemFragment __typename}__typename}fragment NutritionExplorerSectionFragment on Section{_id _type name{locale:en __typename}carouselImage{...ImageFragment __typename}image{...ImageFragment __typename}options{...NutritionExplorerPickerFragment ...NutritionExplorerItemFragment ...NutritionExplorerComboFragment ...on Section{_id _type name{locale:en __typename}options{...NutritionExplorerPickerFragment ...NutritionExplorerItemFragment ...on Section{_type _id options{...NutritionExplorerPickerFragment ...NutritionExplorerItemFragment __typename}__typename}__typename}__typename}__typename}__typename}fragment FilterGroupFragment on FilterGroup{_type description{locale:en __typename}filters{...FilterFragment __typename}__typename}fragment FilterFragment on Filter{_type description{locale:en __typename}conditions{...ConditionAllergenFragment ...ConditionNutritionFragment ...ConditionParentCategoryFragment ...ConditionItemOneOfFragment __typename}__typename}fragment ConditionAllergenFragment on ConditionAllergen{_type allergenIdentifier comparisonOperator comparisonValue __typename}fragment ConditionNutritionFragment on ConditionNutrition{_type nutritionIdentifier comparisonOperator comparisonValue __typename}fragment ConditionParentCategoryFragment on ConditionParentCategory{_type parentCategory{...on Section{_id __typename}...on Picker{_id __typename}__typename}__typename}fragment ConditionItemOneOfFragment on ConditionItemOneOf{_type items{...NutritionExplorerItemFragment __typename}__typename}fragment VideoFileFragment on File{asset{assetId path url __typename}__typename}fragment ItemFragment on Item{_id _type name{locale:en __typename}description{localeRaw:enRaw __typename}legalInformation{localeRaw:enRaw __typename}image{...MenuImageFragment __typename}imageDescription{locale:en __typename}imagesByChannels{...ImagesByChannelsFragment __typename}rewardEligible isDummyItem labelAsPerPerson nutrition{...NutritionFragment __typename}additionalItemInformation{...AdditionalItemInformationFragment __typename}nutritionWithModifiers{...NutritionFragment __typename}productSize allergens{...AllergensFragment __typename}options{...ItemOptionFragment __typename}productHierarchy{L1 L2 L3 L4 L5 __typename}menuObjectSettings{limitPerOrder __typename}channelExclusions{delivery pickup __typename}__typename}fragment MenuImageFragment on Image{hotspot{x y height width __typename}crop{top bottom left right __typename}asset{metadata{lqip __typename}_id __typename}__typename}fragment ImagesByChannelsFragment on ImagesByChannels{imageRestaurant{asset{_id metadata{lqip __typename}__typename}__typename}imageDelivery{asset{_id metadata{lqip __typename}__typename}__typename}__typename}fragment AdditionalItemInformationFragment on AdditionalItemInformation{ingredients{locale:en __typename}additives{locale:en __typename}producerDetails{locale:en __typename}sourcesOfGluten __typename}fragment AllergensFragment on OpAllergen{milk eggs fish peanuts shellfish treeNuts soy wheat mustard sesame celery lupin gluten sulphurDioxide __typename}fragment ItemOptionFragment on ItemOption{name{locale:en __typename}displayGroup{name{locale:en __typename}__typename}componentStyle upsellModifier allowMultipleSelections displayModifierMultiplierName injectDefaultSelection singleChoiceOnly minAmount maxAmount _key type:_type options{_key type:_type name{locale:en __typename}vendorConfigs{...VendorConfigsFragment __typename}pluConfigs{...PluConfigsFragment __typename}default modifierMultiplier{multiplier prefix{locale:en __typename}modifier{name{locale:en __typename}image{...MenuImageFragment __typename}imageDescription{locale:en __typename}__typename}__typename}nutrition{...NutritionFragment __typename}__typename}__typename}fragment VendorConfigsFragment on VendorConfigs{ncr{...VendorConfigFragment __typename}ncrDelivery{...VendorConfigFragment __typename}partner{...VendorConfigFragment __typename}partnerDelivery{...VendorConfigFragment __typename}productNumber{...VendorConfigFragment __typename}productNumberDelivery{...VendorConfigFragment __typename}sicom{...VendorConfigFragment __typename}sicomDelivery{...VendorConfigFragment __typename}qdi{...VendorConfigFragment __typename}qdiDelivery{...VendorConfigFragment __typename}rpos{...VendorConfigFragment __typename}rposDelivery{...VendorConfigFragment __typename}simplyDelivery{...VendorConfigFragment __typename}simplyDeliveryDelivery{...VendorConfigFragment __typename}toshibaLoyalty{...VendorConfigFragment __typename}__typename}fragment VendorConfigFragment on VendorConfig{pluType parentSanityId pullUpLevels constantPlu discountPlu quantityBasedPlu{quantity plu qualifier __typename}multiConstantPlus{quantity plu qualifier __typename}parentChildPlu{plu childPlu __typename}sizeBasedPlu{comboPlu comboSize __typename}__typename}fragment PluConfigsFragment on PluConfigs{_key _type partner{...PluConfigFragment __typename}__typename}fragment PluConfigFragment on PluConfig{_key _type posIntegration{_id _type name __typename}serviceMode vendorConfig{...VendorConfigFragment __typename}__typename}',
    }
    
    base_url = 'https://czqk28jt.apicdn.sanity.io/v2023-08-01/graphql/prod_bk_gb/gen3'
    
    try:
        print("Making request to Burger King GraphQL API...")
        response = requests.post(base_url, params=params, headers=headers, json=json_data)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        json_response = response.json()
        print("API response received successfully")
        # print(json.dumps(json_response, indent=2))  # Uncomment to see full JSON response
        
        # Extract menu data
        try:
            menu_options = json_response['data']['StaticPage']['widgets'][0]['menu']['options']
        except (KeyError, IndexError) as e:
            print(f"Error extracting menu data: {e}")
            return
        
        results = []
        total_items = 0
        
        for category in menu_options:
            try:
                category_name = clean_text(category.get('name', {}).get('locale', 'Unknown Category'))
                print(f"Processing category: {category_name}")
                
                category_products = category.get('options', [])
                
                for product in category_products:
                    try:
                        # Extract product name
                        product_name = clean_text(product.get('name', {}).get('locale', 'Unknown Product'))
                        
                        # Extract nutrition data
                        nutrition_data = {}
                        try:
                            # Try different paths to find nutrition data
                            if len(product) == 9 and 'options' in product:
                                nutrition = product['options'][0]['option'].get('nutritionWithModifiers', {})
                            else:
                                nutrition = product.get('nutritionWithModifiers', {})
                                
                            # If still empty, try main item path
                            if not nutrition and 'options' in product:
                                nutrition = product['options'][0]['option'].get('mainItem', {}).get('nutritionWithModifiers', {})
                                
                            # Clean nutrition data - only include numeric values
                            if nutrition:
                                nutrition_data = {k: v for k, v in nutrition.items() 
                                                if v is not None and not isinstance(v, str)}
                        except (KeyError, IndexError, TypeError):
                            pass
                        
                        # Extract allergen data
                        allergen_list = []
                        try:
                            # Try different paths to find allergen data
                            if len(product) == 9 and 'options' in product:
                                allergens = product['options'][0]['option'].get('allergens', {})
                            else:
                                allergens = product.get('allergens', {})
                                
                            # Convert allergen dict to list of present allergens
                            if allergens:
                                allergen_list = [allergen for allergen, present in allergens.items() 
                                               if present and not isinstance(present, str) and present > 0]
                        except (KeyError, IndexError, TypeError):
                            pass
                        
                        # Create item dictionary
                        item_dict = {
                            'rest_name': 'Burger King',
                            'collection_date': date.today().strftime("%b-%d-%Y"),
                            'category_name': category_name,
                            'product_name': product_name,
                            'allergens': allergen_list,
                        }
                        
                        # Add nutrition data if available
                        if nutrition_data:
                            item_dict.update(nutrition_data)
                            
                        results.append(item_dict)
                        total_items += 1
                        
                    except Exception as e:
                        print(f"Error processing product '{product.get('name', {}).get('locale', 'Unknown')}': {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Error processing category: {str(e)}")
                continue
        
        # Save results to JSON file
        with open(file_burgerking_json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Scraped {total_items} items from {len(menu_options)} categories. Data saved to {file_burgerking_json}.")

        # Save results to CSV file
        if results:
            df = pd.DataFrame(results)
            df.to_csv(file_burgerking_csv, index=False)
            print(f"Data also saved to CSV: {file_burgerking_csv}")
        else:
            print("No data to save to CSV")

    except requests.RequestException as e:
        print(f"Error making API request: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == '__main__':
    crawl_burgerking_nutrition()
