import re
from typing import List, Dict, Any


class FilterEngine:

    
    def __init__(self, config: Dict[str, Any]):


        self.filters = config.get("filters", {})
        
        self.keyword_mode = self.filters.get("keyword_mode", "any")
        
        self.keywords = self.filters.get("keywords", {})
        
        self.action_keys = self.filters.get("action_keys", [])
        
        self.owner_states = self.filters.get("owner_states", [])
        
        self.legal_entity_codes = self.filters.get("legal_entity_codes", [])
    




    def matches_filters(self, trademark: Dict[str, Any]) -> tuple[bool, List[str]]:



        reasons = []
        


        if self.owner_states:
            state_code = trademark.get("stateCountryCode", "")
            if state_code not in self.owner_states:
                return False, []
        




        if self.legal_entity_codes:
            entity_code = trademark.get("entityTypeCode", "")
            if entity_code not in self.legal_entity_codes:
                return False, []
        



        if self.action_keys and "NA" not in self.action_keys:
            pass
        





        keyword_matches = self._check_keywords(trademark)
        
        if self.keyword_mode == "any":



            if keyword_matches:
                reasons.extend(keyword_matches)
                return True, reasons
            return False, []
        elif self.keyword_mode == "all":



            if keyword_matches:
                reasons.extend(keyword_matches)
                return True, reasons
            return False, []
        
        return False, []
    
    def _check_keywords(self, trademark: Dict[str, Any]) -> List[str]:




        matches = []
        


        mark_id_keywords = self.keywords.get("mark_identification", [])
        if mark_id_keywords:
            mark_id = trademark.get("markIdentification", "")
            if self._text_matches_patterns(mark_id, mark_id_keywords):
                matches.append(f"Mark Identification: {mark_id}")
        




        gs_keywords = self.keywords.get("goods_services", [])
        if gs_keywords:
            goods_services = trademark.get("goodsServices", "")
            if self._text_matches_patterns(goods_services, gs_keywords):
                matches.append(f"Goods/Services match")
        



        owner_keywords = self.keywords.get("owner_name", [])
        if owner_keywords:
            owner_name = trademark.get("ownerName", "")
            dba_aka = trademark.get("dbaAkaFormerly", "")
            



            owner_matched = self._text_matches_patterns(owner_name, owner_keywords)
            dba_matched = self._text_matches_patterns(dba_aka, owner_keywords) if dba_aka else False
            
            if owner_matched:
                matches.append(f"Owner Name: {owner_name}")
            elif dba_matched:
                matches.append(f"DBA/AKA Name: {dba_aka}")
        



        email_keywords = self.keywords.get("email_addresses", [])
        if email_keywords:
            attorney_emails = trademark.get("attorneyEmailAddresses", [])
            correspondant_emails = trademark.get("correspondantEmailAddresses", [])
            all_emails = attorney_emails + correspondant_emails
            
            for email in all_emails:
                if self._text_matches_patterns(email, email_keywords):
                    matches.append(f"Email: {email}")
                    break
        
        return matches






    def _text_matches_patterns(self, text: str, patterns: List[str]) -> bool:





        if not text or not patterns:
            return False
        
        text_lower = text.lower()
        
        for pattern in patterns:
            pattern_lower = pattern.lower()
            
            escaped = re.escape(pattern_lower)
            



            regex_pattern = escaped.replace(r'\*', '.*')
            regex_pattern = f"^{regex_pattern}$"
            
            try:
                if re.search(regex_pattern, text_lower):
                    return True
            except re.error:



                pattern_clean = pattern_lower.replace("*", "")
                if pattern_clean in text_lower:
                    return True
        
        return False
    
    def filter_trademarks(self, trademarks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:





        filtered = []
        
        for tm in trademarks:
            matches, reasons = self.matches_filters(tm)
            if matches:
                tm["match_reasons"] = reasons
                filtered.append(tm)
        



        
        return filtered
