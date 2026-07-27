import requests
import datetime
from django.core.cache import cache

class HolidayService:
    """
    Serviço de alta performance para buscar e cachear feriados.
    """
    @staticmethod
    def get_petrolina_holidays(year):
        cache_key = f'holidays_petrolina_{year}'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
            
        holidays_list = []
        
        # Executa requisição remota para captação de feriados nacionais na base da Brasil API.
        try:
            response = requests.get(f'https://brasilapi.com.br/api/feriados/v1/{year}', timeout=5)
            if response.status_code == 200:
                try:
                    national_data = response.json()
                    for item in national_data:
                        holidays_list.append({
                            'date': item['date'],
                            'name': item['name'],
                            'type': 'NACIONAL'
                        })
                except ValueError:
                    HolidayService._append_national_fallback(holidays_list, year)
            else:
                HolidayService._append_national_fallback(holidays_list, year)
        except requests.exceptions.RequestException:
            # Implementação de tratamento para eventuais recusas de conexão da API remota.
            HolidayService._append_national_fallback(holidays_list, year)
            
        # Procedimento de busca de feriados de abrangência estadual (Pernambuco).
        holidays_list.append({
            'date': f'{year}-03-06',
            'name': 'Data Magna de Pernambuco',
            'type': 'ESTADUAL'
        })
        
        # Procedimento de busca de feriados de abrangência municipal (Petrolina).
        municipal_holidays = [
            ('06-24', 'São João'),
            ('08-15', 'Nossa Senhora Rainha dos Anjos'),
            ('09-21', 'Emancipação Política de Petrolina')
        ]
        
        for md, name in municipal_holidays:
            holidays_list.append({
                'date': f'{year}-{md}',
                'name': name,
                'type': 'MUNICIPAL'
            })
            
        # Armazena os dados no provedor de cache por tempo indeterminado (conforme compatibilidade do backend).
        cache.set(cache_key, holidays_list, timeout=None)
        
        return holidays_list

    @staticmethod
    def _append_national_fallback(holidays_list, year):
        # Mecanismo autônomo (hardcoded) para sustentação dos dados caso a Brasil API fique inoperante.
        national_dates = [
            ('01-01', 'Confraternização Universal'),
            ('04-21', 'Tiradentes'),
            ('05-01', 'Dia do Trabalhador'),
            ('09-07', 'Independência do Brasil'),
            ('10-12', 'Nossa Senhora Aparecida'),
            ('11-02', 'Finados'),
            ('11-15', 'Proclamação da República'),
            ('12-25', 'Natal'),
        ]
        for md, name in national_dates:
            holidays_list.append({
                'date': f'{year}-{md}',
                'name': name,
                'type': 'NACIONAL'
            })
