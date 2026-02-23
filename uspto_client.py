
import requests
import time
from typing import List, Dict, Optional


class USPTOClient:


    
    BASE_URL = "https://tsdrapi.uspto.gov/ts/cd/caseMultiStatus/sn"
    
    def __init__(self, api_key: str, rate_limit_delay: float = 1.0):




        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            "USPTO-API-KEY": api_key,
            "Accept": "application/json"
        })
    
    def query_batch(self, serial_numbers: List[int]) -> Optional[Dict]:





        if len(serial_numbers) > 20:
            raise ValueError(" !!! Max: Only 20 serial Nos. per API Pull")
        




        ids_param = ",".join(str(sn) for sn in serial_numbers)
        url = f"{self.BASE_URL}?ids={ids_param}"
    




        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(" !!! Rate limit hit ...")
                time.sleep(10)
                return None
            else:
                print(f" !!! API says {response.status_code}")
                return None


     
        except requests.exceptions.RequestException as e:
            print(f" !!! Error w/ API: {e}")
            return None
        finally:
            time.sleep(self.rate_limit_delay)
   







    def extract_trademark_data(self, response: Dict) -> List[Dict]:
 
        trademarks = []
        
        if not response or "transactionList" not in response:
            return trademarks
        
        transaction_list = response.get("transactionList", [])
        





        for transaction in transaction_list:
            trademark_list = transaction.get("trademarks", [])
            
            for tm in trademark_list:
                try:



                    status = tm.get("status", {})
                    parties = tm.get("parties", {})
                    



                    owner_groups = parties.get("ownerGroups", {})
                    owner_list = owner_groups.get("10", [])
                    owner_info = owner_list[0] if owner_list else {}
                    



                    correspondence = status.get("correspondence", {})
                    attorney_email = correspondence.get("attorneyEmail", {})
                    correspondant_email = correspondence.get("correspondantEmail", {})
                    



                    address_state_country = owner_info.get("addressStateCountry", {})
                    state_country = address_state_country.get("stateCountry", {})
                    iso_info = address_state_country.get("iso", {})
                    



                    entity_type = owner_info.get("entityType", {})
                    entity_code_raw = entity_type.get("code")
                    entity_code_str = f"{entity_code_raw:02d}" if entity_code_raw else ""





                    trademark_data = {
                        "serialNumber": status.get("serialNumber"),
                        "filingDate": status.get("filingDate"),
                        "status": status.get("status"),
                        "markIdentification": status.get("markElement"),
                        "ownerName": owner_info.get("name"),
                        "entityTypeCode": entity_code_str,
                        "stateCountryCode": state_country.get("code"),
                        "isoCode": iso_info.get("code"),
                        "attorneyEmailAddresses": attorney_email.get("addresses", []),
                        "correspondantEmailAddresses": correspondant_email.get("addresses", []),
                        "dbaAkaFormerly": owner_info.get("dbaAkaFormerly"),
                        "goodsServices": self._extract_goods_services(tm),
                        "markImageUrl": self._extract_mark_image(tm)
                    }
                    



                    if trademark_data["serialNumber"]:
                        trademarks.append(trademark_data)
                    
                except Exception as e:
                    print(f" !!! Error w/ trademark data pull: {e}")
                    continue
        
        return trademarks




    def _extract_goods_services(self, trademark: Dict) -> str:

        try:
            gs_list = trademark.get("gsList", [])
            
            goods_services = []
            for item in gs_list:
                description = item.get("description", "")
                if description:
                    goods_services.append(description)
            
            return " | ".join(goods_services)
        except:
            return ""






    #def _extract_mark_image(self, trademark: Dict) -> str:



        #try:
            #status = trademark.get("status", {})
            #mark_drawing = status.get("markDrawing", {})
            #return mark_drawing.get("imageUrl", "")
        #except:
            #return ""
