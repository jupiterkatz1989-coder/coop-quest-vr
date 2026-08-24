import unittest
from tools.steam_catalog import COOP_IDS, VR_OPTIONAL_ID, VR_REQUIRED_ID, classify, new_game, update_game


class SteamCatalogTests(unittest.TestCase):
    def sample(self, categories):
        return {
            'name': 'Juego de prueba VR', 'type': 'game', 'categories': categories,
            'genres': [{'description': 'Acción'}], 'header_image': 'https://example.com/header.jpg',
            'price_overview': {'final': 1999, 'currency': 'EUR', 'discount_percent': 20},
            'release_date': {'coming_soon': False, 'date': '24 Aug, 2026'},
        }

    def test_official_ids_are_strict(self):
        self.assertEqual(COOP_IDS, {9, 38, 39})
        self.assertEqual((VR_OPTIONAL_ID, VR_REQUIRED_ID), (53, 54))

    def test_update_preserves_unknown_player_limit_and_sets_eur(self):
        data = self.sample([{'id': 38, 'description': 'Cooperativo en línea'}, {'id': 54, 'description': 'Solo para RV'}])
        game = new_game(data, 123)
        update_game(game, data, {'total_reviews': 100, 'total_positive': 80}, 123, '2026-08-24', False, False)
        classify(game)
        self.assertIsNone(game['coop']['max_jugadores'])
        self.assertEqual(game['steam_vr_modo'], 'obligatorio')
        self.assertEqual(game['clasificacion_plataforma'], 'solo_pcvr')
        self.assertEqual(game['precio_actual']['moneda'], 'EUR')
        self.assertTrue(game['precio_actual']['realmente_recotizado'])

    def test_cross_store_is_both(self):
        data = self.sample([{'id': 9, 'description': 'Cooperativo'}, {'id': 53, 'description': 'Compatible con RV'}])
        game = new_game(data, 456)
        game['plataformas'].append({'tipo': 'Meta Quest Store', 'modo_quest': 'nativo', 'url': 'https://example.com/meta'})
        update_game(game, data, {}, 456, '2026-08-24', False, False)
        classify(game)
        self.assertEqual(game['clasificacion_plataforma'], 'ambos')
        self.assertEqual(game['steam_vr_modo'], 'opcional')


if __name__ == '__main__':
    unittest.main()
