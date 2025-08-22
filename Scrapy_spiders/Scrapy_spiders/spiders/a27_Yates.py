from datetime import date

import scrapy


class A27YatesSpider(scrapy.Spider):
    name = '27_Yates'
    allowed_domains = ['tkmenus.com']
    start_urls = ['https://tkmenus.com/greattraditionalpubs']

    def parse(self, response):
        items = response.xpath('//div[@class="k10-l-grid"]')
        for item in items:
            yield {
                'collection_date': date.today().strftime("%b-%d-%Y"),
                'rest_name': "Yate's",
                'menu_section': item.xpath('./ancestor::section[@class="k10-course grid-item"]/h2/text()').get(),
                'item_name': item.xpath('.//span[@class="k10-recipe__name-val"]/text()').get(),
                'item_description': item.xpath('normalize-space(.//p[@class="k10-recipe__desc"]/text())').get(),
                'allergens': [string.strip() for string in
                              item.xpath('.//div[@class="k10-recipe__labels-wrapper-content"]/div/text()').getall()],
                'kcal': self.get_nutrient_value(item, "Energy (kcal)"),
                'kj': self.get_nutrient_value(item, "Energy (kJ)", replace_comma=True),
                'protein': self.get_nutrient_value(item, "Protein (g)"),
                'carb': self.get_nutrient_value(item, "Carbs (g)"),
                'sugar': self.get_nutrient_value(item, "Sugars (g)"),
                'fat': self.get_nutrient_value(item, "Fat (g)"),
                'satfat': self.get_nutrient_value(item, "Saturates (g)"),
                'salt': self.get_nutrient_value(item, "Salt (g)"),
            }

    def get_nutrient_value(self, item, nutrient_name, replace_comma=False):
        """
        Extracts the nutrient value from the item.

        Args:
            item: The Scrapy item (response.xpath object).
            nutrient_name: The name of the nutrient to extract.
            replace_comma: Whether to replace commas with empty strings.

        Returns:
            The nutrient value as a string, or None if not found.
        """
        xpath_query = f'.//div[@class="k10-recipe__nutrients-item"]/span[contains(text(),"{nutrient_name}")]/following-sibling::span/text()'
        value = item.xpath(xpath_query).get()

        if value is not None:
            if replace_comma:
                value = value.replace(',', '')
            return value
        else:
            return None