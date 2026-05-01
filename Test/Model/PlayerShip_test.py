import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from Model.PlayerShip import PlayerShip
from mock import patch, MagicMock
from PIL import Image
import time
import numpy as np

RESIZED_FIXTURE = 'Test/Model/TestResizedWindow.png'
RESIZED_TEST_TITLE_BAR = 45
RESIZED_TEST_LEFT_BORDER = 8

class TestPlayerShip(unittest.TestCase):
    @patch('Model.PlayerShip.pyautogui.screenshot')
    @patch('Model.Masker.gw.getWindowsWithTitle')
    @patch('Model.PlayerShip.gw.getWindowsWithTitle')
    def setUp(self, mock_get_windows, mock_masker_get_windows, mock_screenshot):
        # Mock the FTL window
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_window.left = 0
        mock_window.top = 0
        mock_get_windows.return_value = [mock_window]
        mock_masker_get_windows.return_value = [mock_window]

        self.player_ship = PlayerShip()
        self.player_ship.TITLE_BAR_HEIGHT = 0  # Set title bar height to 0 for testing
        self.player_ship.WINDOW_LEFT_BORDER = 0  # Set left border to 0 for testing

    def test_detect_health(self):
        # Replace screenshot with a preset image TestImage1.jpg that has a known health bar state
        test_image = Image.open('Test/Model/TestImage1.jpg')
        
        health = self.player_ship.detect_health(test_image  )
        # Assuming TestImage1.jpg has 25 hit points, we can assert that the detected health is correct
        self.assertEqual(health, 25)
        self.assertEqual(self.player_ship.health, 25)

    def test_detect_health_yellow(self):
        # Replace screenshot with a preset image TestYellowBar. that has a known health bar state with yellow pixels
        test_image = Image.open('Test/Model/TestYellowBar.png')
        
        health = self.player_ship.detect_health(test_image)
        # Assuming TestYellowBar.png has 18 hit points, we can assert that the detected health is correct
        self.assertEqual(health, 18)
        self.assertEqual(self.player_ship.health, 18)

    def test_detect_health_red(self):
        # Replace screenshot with a preset image TestImage2.pngthat has a known health bar state with red pixels
        # The border on test image 2 has flashed red, but should not be counted as a hit point
        test_image = Image.open('Test/Model/TestImage2.png')
        
        health = self.player_ship.detect_health(test_image)
        # Assuming TestImage2.png has 6 hit points, we can assert that the detected health is correct
        self.assertEqual(health, 6)
        self.assertEqual(self.player_ship.health, 6)

    def test_detect_shield(self):
        # Replace screenshot with a preset image TestImage1.jpg that has a known shield bar state
        test_image = Image.open('Test/Model/TestImage1.jpg')
        
        shield = self.player_ship.detect_shield(test_image)
        # Assuming TestImage1.jpg has 2 shield points, we can assert that the detected shield is correct
        self.assertEqual(shield, 2)
        self.assertEqual(self.player_ship.shield, 2)
        
    def test_detect_shield_broken(self):
        # screenshot is the same as detect_health_yellow, which has a broken shield bar with 0 shield points
        test_image = Image.open('Test/Model/TestYellowBar.png')
        shield = self.player_ship.detect_shield(test_image)
        # Assuming TestYellowBar.png has 0 shield points, we can assert that the detected shield is correct
        self.assertEqual(shield, 0)
        self.assertEqual(self.player_ship.shield, 0)

    @patch('Model.Masker.gw.getWindowsWithTitle')
    def test_detect_rooms_ignores_thin_internal_split_lines(self, mock_masker_get_windows):
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_window.left = 0
        mock_window.top = 0
        mock_masker_get_windows.return_value = [mock_window]

        self.player_ship.ROOM_REGION = (0, 0, 200, 200)
        test_image = Image.new('RGB', (200, 200), color='black')

        # One room with a thin internal gap that should not split into two contours.
        room_mask = np.zeros((200, 200), dtype=np.uint8)
        room_mask[20:180, 20:180] = 255
        room_mask[20:180, 100:102] = 0
        self.player_ship.mask_region = MagicMock(return_value=room_mask)

        rooms = self.player_ship.detect_rooms(test_image)

        self.assertEqual(len(rooms), 1)
        x, y, w, h = rooms[0].bounds
        self.assertTrue(x <= 20 and y <= 20)
        self.assertTrue(w >= 155 and h >= 155)

    @patch('Model.Masker.gw.getWindowsWithTitle')
    def test_detect_rooms_detects_correct_amount_of_rooms(self, mock_masker_get_windows):
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_window.left = 0
        mock_window.top = 0
        mock_masker_get_windows.return_value = [mock_window]

        test_image = Image.open('Test/Model/TestYellowBar.png')
        rooms = self.player_ship.detect_rooms(test_image)
        # Assuming TestYellowBar.png has 19 rooms, we can assert that the detected rooms are correct
        self.assertEqual(len(rooms), 19)



class TestPlayerShipResizedWindow(unittest.TestCase):
    @patch('Model.PlayerShip.pyautogui.screenshot')
    @patch('Model.Masker.gw.getWindowsWithTitle')
    @patch('Model.PlayerShip.gw.getWindowsWithTitle')
    def setUp(self, mock_get_windows, mock_masker_get_windows, mock_screenshot):
        # Use the resized fixture dimensions as the mocked window geometry.
        with Image.open(RESIZED_FIXTURE) as fixture_image:
            self.fixture_image = fixture_image.copy()
        fixture_width, fixture_height = self.fixture_image.size

        mock_window = MagicMock()
        mock_window.width = fixture_width
        mock_window.height = fixture_height
        mock_window.left = 0
        mock_window.top = 0
        mock_get_windows.return_value = [mock_window]
        mock_masker_get_windows.return_value = [mock_window]

        def _mock_capture(region=None):
            if region is None:
                return self.fixture_image.copy()
            left, top, width, height = region
            return self.fixture_image.crop((left, top, left + width, top + height))

        mock_screenshot.side_effect = _mock_capture

        # screenshot() normalizes to 1280x720; use that output in assertions.
        self.player_ship = PlayerShip()
        self.player_ship.TITLE_BAR_HEIGHT = RESIZED_TEST_TITLE_BAR
        self.player_ship.WINDOW_LEFT_BORDER = RESIZED_TEST_LEFT_BORDER
        self.test_image = self.player_ship.screenshot()


    def test_detect_health_resized_fixture(self):
        health = self.player_ship.detect_health(self.test_image)
        self.assertEqual(health, 30)
        self.assertEqual(self.player_ship.health, 30)

    def test_detect_shield_resized_fixture(self):
        shield = self.player_ship.detect_shield(self.test_image)
        self.assertEqual(shield, 1)
        self.assertEqual(self.player_ship.shield, 1)

    
    @patch('Model.Masker.gw.getWindowsWithTitle')
    def test_detect_rooms_detects_correct_amount_of_rooms_in_resized_fixture(self, mock_masker_get_windows):
        mock_window = MagicMock()
        mock_window.width = self.fixture_image.size[0]
        mock_window.height = self.fixture_image.size[1]
        mock_window.left = 0
        mock_window.top = 0
        mock_masker_get_windows.return_value = [mock_window]

        test_image = self.test_image
        rooms = self.player_ship.detect_rooms(test_image)
        # Assuming the resized fixture has 17 rooms, we can assert that the detected rooms are correct
        self.assertEqual(len(rooms), 17)

