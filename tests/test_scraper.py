# test_scraper.py

import unittest
import os, sys
from bs4 import BeautifulSoup


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from scraper import extract_vehicle_data

class TestScraper(unittest.TestCase):

    def test_extract_vehicle_data_sample1(self):
        # HTML snippet for the first vehicle card example
        html_content = '''
        <div id="vehicle_card_0" alt="Land Rover Range Rover Evoque 2026" class="ewtqiv33 css-dkiyok e11el9oi0">
            <div class="css-gch8ic e19qstch16">
                <div class="css-102djdw e19qstch10">
                    <div class="css-3oc9y8 e19qstch20">SUV</div>
                </div>
            </div>
            <a rel="noreferrer" href="/land-rover/range-rover-evoque/" target="_self" type="unstyledAll" class="css-z66djy ewtqiv30">2026 Land Rover Range Rover Evoque</a>
            <div style="flex:auto" class="css-ssaa7u ewtqiv32">
                <div class="css-kpig8u e19qstch21">
                    <div class="css-1gkcjku e19qstch5">
                        <div style="pointer-events:auto" class="css-gk1xze ex4y58i4">
                            <a type="heading" href="/land-rover/range-rover-evoque/" target="_self" class="css-1et62um e1ez57g00">
                                <h2 class="css-iqcfy5 e148eed12">2026 Land Rover Range Rover Evoque</h2>
                            </a>
                        </div>
                    </div>
                </div>
                <div class="css-15j21fj e19qstch15">
                    <div class="css-n59ln1 e181er9y2">
                        <div class="css-1d3w5wq e181er9y1">
                            <div direction="horizontal" class="css-15ums5i e181er9y0">
                                <div class="css-fpbjth e151py7u1">$51,175</div>
                                <div class="css-1xdhyk6 e1ma5l2g0">
                                    <div class="css-gurmh7 e1ma5l2g4">
                                        <div class="css-tpw6mp e1ma5l2g3">Starting Price</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="css-14q4cew e19qstch18">
                    <hr class="css-1ai9wuw e1lulwj20" role="presentation" aria-hidden="true" tabindex="-1">
                    <div class="css-1ouitaz ex4y58i1">
                        <div>
                            <div class="css-hryd08">Expert (<span class="css-1rttn8x">N/A</span>)</div>
                        </div>
                        <div>
                            <div class="css-1p1bpqh">
                                <div class="css-1c7qqqr">3.4</div>
                                <div class="css-hryd08">Consumer</div>
                            </div>
                        </div>
                    </div>
                    <hr class="css-1ai9wuw e1lulwj20" role="presentation" aria-hidden="true" tabindex="-1">
                    <div class="css-n59ln1 e181er9y2">
                        <div class="css-1d3w5wq e181er9y1">
                            <div direction="horizontal" class="css-15ums5i e181er9y0">
                                <div class="css-fpbjth e151py7u1">22 MPG</div>
                                <div class="css-1xdhyk6 e1ma5l2g0">
                                    <div class="css-gurmh7 e1ma5l2g4">
                                        <div class="css-tpw6mp e1ma5l2g3">Combined Fuel Economy</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        card = soup.find('div', id='vehicle_card_0')  # Adjusted line
        data = extract_vehicle_data(card)
        expected_data = {
            'id': 'vehicle_card_0',
            'name': '2026 Land Rover Range Rover Evoque',
            'make': 'Land',
            'model': 'Rover Range Rover Evoque',
            'year': '2026',
            'category': 'SUV',
            'name_verification': '2026 Land Rover Range Rover Evoque',
            'starting_price': '$51,175',
            'fuel_economy': '22 MPG',
            'expert_rating': 'N/A',
            'consumer_rating': '3.4',
            'description': 'N/A'
        }
        self.assertEqual(data, expected_data)

    def test_extract_vehicle_data_sample2(self):
        # HTML snippet for the second vehicle card example
        html_content = '''
        <div id="vehicle_card_33" alt="Suzuki Samurai 1992" class="ewtqiv33 css-dkiyok e11el9oi0">
            <div class="css-gch8ic e19qstch16">
                <div class="css-102djdw e19qstch10">
                    <div class="css-3oc9y8 e19qstch20">SUV</div>
                </div>
            </div>
            <a rel="noreferrer" href="/suzuki/samurai/1992/" target="_self" type="unstyledAll" class="css-z66djy ewtqiv30">1992 Suzuki Samurai</a>
            <div style="flex:auto" class="css-ssaa7u ewtqiv32">
                <div class="css-kpig8u e19qstch21">
                    <div class="css-1gkcjku e19qstch5">
                        <div style="pointer-events:auto" class="css-gk1xze ex4y58i4">
                            <a type="heading" href="/suzuki/samurai/1992/" target="_self" class="css-1et62um e1ez57g00">
                                <h2 class="css-iqcfy5 e148eed12">1992 Suzuki Samurai</h2>
                            </a>
                        </div>
                    </div>
                </div>
                <div class="css-15j21fj e19qstch15">
                    <div class="css-n59ln1 e181er9y2">
                        <div class="css-1d3w5wq e181er9y1">
                            <div direction="horizontal" class="css-15ums5i e181er9y0">
                                <div class="css-fpbjth e151py7u1">$2,731</div>
                                <div class="css-1xdhyk6 e1ma5l2g0">
                                    <div class="css-gurmh7 e1ma5l2g4">
                                        <div class="css-tpw6mp e1ma5l2g3">Starting Price</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="css-14q4cew e19qstch18">
                    <hr class="css-1ai9wuw e1lulwj20" role="presentation" aria-hidden="true" tabindex="-1">
                    <div class="css-1ouitaz ex4y58i1">
                        <div>
                            <div class="css-hryd08">Expert (<span class="css-1rttn8x">N/A</span>)</div>
                        </div>
                        <div>
                            <div class="css-1p1bpqh">
                                <div class="css-1c7qqqr">4.5</div>
                                <div class="css-hryd08">Consumer</div>
                            </div>
                        </div>
                    </div>
                    <hr class="css-1ai9wuw e1lulwj20" role="presentation" aria-hidden="true" tabindex="-1">
                    <div class="css-n59ln1 e181er9y2">
                        <div class="css-1d3w5wq e181er9y1">
                            <div direction="horizontal" class="css-15ums5i e181er9y0">
                                <div class="css-fpbjth e151py7u1">25 MPG</div>
                                <div class="css-1xdhyk6 e1ma5l2g0">
                                    <div class="css-gurmh7 e1ma5l2g4">
                                        <div class="css-tpw6mp e1ma5l2g3">Combined Fuel Economy</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        card = soup.find('div', id='vehicle_card_33')  # Adjusted line
        data = extract_vehicle_data(card)
        expected_data = {
            'id': 'vehicle_card_33',
            'name': '1992 Suzuki Samurai',
            'make': 'Suzuki',
            'model': 'Samurai',
            'year': '1992',
            'category': 'SUV',
            'name_verification': '1992 Suzuki Samurai',
            'starting_price': '$2,731',
            'fuel_economy': '25 MPG',
            'expert_rating': 'N/A',
            'consumer_rating': '4.5',
            'description': 'N/A'
        }
        self.assertEqual(data, expected_data)

if __name__ == '__main__':
    unittest.main()
