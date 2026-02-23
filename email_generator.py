import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime


class EmailGenerator:


    
    def __init__(self, email_config: Dict[str, Any]):



        self.smtp_server = email_config.get("smtp_server")
        self.smtp_port = email_config.get("smtp_port")
        self.sender_email = email_config.get("sender_email")
        self.sender_password = email_config.get("sender_password")
        self.recipient_emails = email_config.get("recipient_emails", [])
#self.api_key = email_config.get("api_key", "")  # For fetching images
    
    def _fetch_trademark_image(self, serial_number: int) -> str:






    def generate_html_digest(self, matches: List[Dict[str, Any]], batch_info: Dict[str, Any]) -> str:
  



        num_matches = len(matches)
        start_sn = batch_info.get("start_sn", "N/A")
        end_sn = batch_info.get("end_sn", "N/A")
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   





        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #003366;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .summary {{
                    background-color: #f4f4f4;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .trademark {{
                    border: 1px solid #ddd;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    background-color: #fff;
                }}
                .trademark:hover {{
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .trademark-header {{
                    background-color: #e8f4f8;
                    padding: 10px;
                    margin: -20px -20px 15px -20px;
                    border-radius: 5px 5px 0 0;
                    font-weight: bold;
                    font-size: 1.1em;
                }}
                .field {{
                    margin-bottom: 10px;
                }}
                .field-label {{
                    font-weight: bold;
                    color: #003366;
                    display: inline-block;
                    min-width: 180px;
                }}
                .field-value {{
                    display: inline-block;
                }}
                .match-reasons {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 10px;
                    margin-top: 10px;
                }}
                .mark-image {{
                    max-width: 200px;
                    margin: 10px 0;
                    border: 1px solid #ddd;
                    padding: 5px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #ddd;
                    font-size: 0.9em;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Trademark Monitoring Alert</h1>
                <p>New trademark matches found</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Matches Found:</strong> {num_matches}</p>
                <p><strong>Serial Number Range:</strong> {start_sn} - {end_sn}</p>
                <p><strong>Generated:</strong> {date}</p>
            </div>
            
            <h2>Matched Trademarks</h2>
        """




      
        for i, tm in enumerate(matches, 1):
            html += self._generate_trademark_html(tm, i)
        
        html += f"""
            <div class="footer">
                <p>Total trademarks processed across this batch: {batch_info.get('total_processed', 0)}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    




    def _generate_trademark_html(self, trademark: Dict[str, Any], index: int) -> str:




        sn = trademark.get("serialNumber", "N/A")
        
        html = f"""
        <div class="trademark">
            <div class="trademark-header">
                Match #{index} - Serial Number: {sn}
            </div>
        """
        
# Trademark Link - Always provide USPTO TSDR link (image fetch killed)
        html += f"""
            <div class="field" style="text-align: center; margin: 15px 0; padding: 15px; background-color: #e8f4f8; border: 1px solid #b3dce6; border-radius: 5px;">
                <a href="https://tsdr.uspto.gov/#caseNumber={sn}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch" 
                   target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #003366; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                   View Trademark Details
                </a>
            </div>
        """
        



        if trademark.get("markIdentification"):
            html += f"""
            <div class="field">
                <span class="field-label">Mark:</span>
                <span class="field-value">{self._escape_html(trademark.get("markIdentification", "N/A"))}</span>
            </div>
            """
        
        if trademark.get("ownerName"):
            html += f"""
            <div class="field">
                <span class="field-label">Owner:</span>
                <span class="field-value">{self._escape_html(trademark.get("ownerName", "N/A"))}</span>
            </div>
            """
        


        if trademark.get("status"):
            html += f"""
            <div class="field">
                <span class="field-label">Status:</span>
                <span class="field-value">{self._escape_html(trademark.get("status", "N/A"))}</span>
            </div>
            """
        
        if trademark.get("filingDate"):
            html += f"""
            <div class="field">
                <span class="field-label">Filing Date:</span>
                <span class="field-value">{trademark.get("filingDate", "N/A")}</span>
            </div>
            """
        



        if trademark.get("stateCountryCode") or trademark.get("isoCode"):
            html += f"""
            <div class="field">
                <span class="field-label">Location:</span>
                <span class="field-value">{trademark.get("stateCountryCode", "")} {trademark.get("isoCode", "")}</span>
            </div>
            """
        

        if trademark.get("entityTypeCode"):
            html += f"""
            <div class="field">
                <span class="field-label">Entity Type Code:</span>
                <span class="field-value">{trademark.get("entityTypeCode", "N/A")}</span>
            </div>
            """
        

        attorney_emails = trademark.get("attorneyEmailAddresses", [])
        if attorney_emails:
            html += f"""
            <div class="field">
                <span class="field-label">Attorney Email(s):</span>
                <span class="field-value">{", ".join(attorney_emails)}</span>
            </div>
            """
        
        correspondant_emails = trademark.get("correspondantEmailAddresses", [])
        if correspondant_emails:
            html += f"""
            <div class="field">
                <span class="field-label">Correspondant Email(s):</span>
                <span class="field-value">{", ".join(correspondant_emails)}</span>
            </div>
            """
        



        if trademark.get("goodsServices"):
            goods_services = trademark.get("goodsServices", "")[:500]
            html += f"""
            <div class="field">
                <span class="field-label">Goods/Services:</span>
                <span class="field-value">{self._escape_html(goods_services)}</span>
            </div>
            """
        


        match_reasons = trademark.get("match_reasons", [])
        if match_reasons:
            html += """
            <div class="match-reasons">
                <strong>Match Reasons:</strong>
                <ul>
            """
            for reason in match_reasons:
                html += f"<li>{self._escape_html(reason)}</li>"
            html += """
                </ul>
            </div>
            """
        



        html += f"""
            <div class="field" style="margin-top: 15px;">
                <a href="https://tsdr.uspto.gov/#caseNumber={sn}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch" 
                   target="_blank" style="color: #003366; text-decoration: none; font-weight: bold;">
                   View on USPTO TSDR
                </a>
            </div>
        """
        
        html += "</div>"
        
        return html
    
    def _escape_html(self, text: str) -> str:

        if not text:
            return ""
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
 





    def send_email(self, matches: List[Dict[str, Any]], batch_info: Dict[str, Any]) -> bool:

        if not matches:
            print("No matches to send")
            return False
        
        if not self.sender_password:
            print(" !!! No email password // Skipping email send !!! ")
            return False
        
        try:




            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Trademark Alert: {len(matches)} New Match(es) Found"
            msg['From'] = self.sender_email
            msg['To'] = ", ".join(self.recipient_emails)
            



            html_content = self.generate_html_digest(matches, batch_info)
            



            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            






            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {len(self.recipient_emails)} recipient(s)")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
