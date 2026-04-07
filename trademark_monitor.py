#!/usr/bin/env python3

import json
import logging
import os
import re
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pytz
import requests

from config import load_config


# --- logging ---

def setup_logging(cfg):
    log = logging.getLogger(cfg.get("monitor_name", "monitor"))
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    if not log.handlers:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        log.addHandler(sh)
        if cfg.get("log_file"):
            fh = logging.FileHandler(cfg["log_file"])
            fh.setFormatter(fmt)
            log.addHandler(fh)
    return log


# --- state ---

def load_state(state_file):
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_state(state_file, state_dict):
    try:
        with open(state_file, "w") as f:
            json.dump(state_dict, f, indent=2)
    except IOError as e:
        logging.getLogger(__name__).error(f"Failed to save state: {e}")


# --- http ---

def create_session(cfg):
    session = requests.Session()
    session.headers.update({"User-Agent": cfg["user_agent"]})
    return session


# --- email ---

def send_email(cfg, subject, html_content, text_content=None):
    smtp_server = cfg.get("smtp_server")
    smtp_port = cfg.get("smtp_port", 587)
    sender = cfg.get("sender_email")
    password = cfg.get("sender_password")
    recipients = cfg.get("recipient_emails", [])

    if not all([smtp_server, sender, password, recipients]):
        logging.getLogger(__name__).warning("Email not configured")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)

        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        logging.getLogger(__name__).info(f"Email sent to {len(recipients)} recipient(s)")
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Email error: {e}")
        return False


def send_or_save(cfg, subject, html, text, fallback_data, fallback_path, log):
    success = send_email(cfg, subject, html, text)
    if not success and fallback_data and fallback_path:
        log.warning("Email not sent, saving results to file")
        save_json(fallback_data, fallback_path, log)
    return success


# --- file I/O ---

def save_json(data, filepath, log):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        log.info(f"Saved to {filepath}")
    except IOError as e:
        log.error(f"Error saving JSON: {e}")


# --- file cleanup ---

def cleanup_old_files(directory, patterns, keep_count):
    if keep_count <= 0:
        return 0
    total_deleted = 0
    directory = Path(directory)
    for pattern in patterns:
        files_with_ts = []
        for fp in directory.glob(pattern):
            try:
                parts = fp.stem.split("_")
                if len(parts) >= 3:
                    ts_str = f"{parts[-2]}_{parts[-1]}"
                    ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    files_with_ts.append((fp, ts))
            except (ValueError, IndexError):
                continue
        files_with_ts.sort(key=lambda x: x[1], reverse=True)
        for fp, _ in files_with_ts[keep_count:]:
            try:
                fp.unlink()
                total_deleted += 1
            except Exception:
                continue
    return total_deleted


# --- output ---

def ensure_output_dir(path):
    d = Path(path)
    d.mkdir(exist_ok=True)
    return d


# --- run wrapper ---

def run_monitor(cfg, work_fn):
    log = setup_logging(cfg)
    start_time = datetime.now()

    log.info("=" * 60)
    log.info(f"{cfg['monitor_name']} started at {start_time}")
    log.info("=" * 60)

    state = load_state(cfg["state_file"])
    session = create_session(cfg)
    output_dir = ensure_output_dir(cfg["data_directory"]) if cfg.get("data_directory") else None

    new_state = work_fn(cfg, state, session, output_dir, log)

    if new_state:
        new_state["last_run"] = start_time.isoformat()
        save_state(cfg["state_file"], new_state)

    if output_dir and cfg.get("cleanup_patterns"):
        cleanup_old_files(output_dir, cfg["cleanup_patterns"], cfg.get("keep_files", 2))

    elapsed = datetime.now() - start_time
    log.info("=" * 60)
    log.info(f"Completed in {elapsed.total_seconds():.2f}s")
    log.info("=" * 60)


# --- email css ---

BASE_CSS = """
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.header { color: white; padding: 20px; text-align: center; }
.summary { padding: 15px; margin: 20px 0; }
.field { margin: 5px 0; }
.label { font-weight: bold; display: inline-block; width: 150px; }
.value { color: #555; }
.footer { margin-top: 30px; padding: 15px; text-align: center; color: #7f8c8d; font-size: 12px; }
"""

TRADEMARK_CSS = BASE_CSS + """
.header { background-color: #003366; border-radius: 5px; margin-bottom: 20px; }
.summary { background-color: #f4f4f4; border-radius: 5px; margin-bottom: 20px; }
.trademark { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 5px; background-color: #fff; }
.trademark:hover { box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.trademark-header { background-color: #e8f4f8; padding: 10px; margin: -20px -20px 15px -20px; border-radius: 5px 5px 0 0; font-weight: bold; font-size: 1.1em; }
.field-label { font-weight: bold; color: #003366; display: inline-block; min-width: 180px; }
.field-value { display: inline-block; }
.match-reasons { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin-top: 10px; }
.footer { margin-top: 30px; padding-top: 20px; border-top: 2px solid #ddd; font-size: 0.9em; color: #666; }
"""


# --- rate limit ---

def get_rate_limit(cfg, log):
    override = cfg.get("trademark_rate_limit_delay")
    if override is not None:
        log.info(f"Custom rate-limit from config: {override}s per request")
        return override

    est = pytz.timezone("US/Eastern")
    hour = datetime.now(est).hour
    if hour >= 22 or hour < 5:
        log.info("Off-peak time - faster rate (120 req/min)")
        return 0.5
    else:
        log.info("Peak time - standard rate (60 req/min)")
        return 1.0


# --- state helpers ---

def get_next_sn(state):
    return state.get("last_processed_sn", 0) + 1


def update_position(state, sn, reason="batch_complete"):
    state["last_processed_sn"] = sn
    state["last_updated"] = datetime.now().isoformat()
    if reason == "match_found":
        state["total_matches"] = state.get("total_matches", 0) + 1
    elif reason == "batch_complete":
        state["total_batches_processed"] = state.get("total_batches_processed", 0) + 1
    return state


# --- USPTO client ---

class USPTOClient:

    BASE_URL = "https://tsdrapi.uspto.gov/ts/cd/caseMultiStatus/sn"

    def __init__(self, session, api_key, rate_limit_delay=1.0):
        self.session = session
        self.session.headers.update({
            "USPTO-API-KEY": api_key,
            "Accept": "application/json",
        })
        self.rate_limit_delay = rate_limit_delay

    def query_batch(self, serial_numbers):
        if len(serial_numbers) > 20:
            raise ValueError("Max 20 serial numbers per API call")

        ids_param = ",".join(str(sn) for sn in serial_numbers)
        url = f"{self.BASE_URL}?ids={ids_param}"

        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                print("Rate limit hit, backing off ...")
                time.sleep(10)
                return None
            else:
                print(f"API returned {resp.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"API error: {e}")
            return None
        finally:
            time.sleep(self.rate_limit_delay)

    def extract_trademark_data(self, response):
        trademarks = []
        if not response or "transactionList" not in response:
            return trademarks

        for transaction in response.get("transactionList", []):
            for tm in transaction.get("trademarks", []):
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

                    data = {
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
                    }
                    if data["serialNumber"]:
                        trademarks.append(data)
                except Exception as e:
                    print(f"Error extracting trademark data: {e}")
                    continue
        return trademarks

    def _extract_goods_services(self, trademark):
        try:
            gs_list = trademark.get("gsList", [])
            descriptions = [item.get("description", "") for item in gs_list if item.get("description")]
            return " | ".join(descriptions)
        except Exception:
            return ""


# --- filter engine ---

class FilterEngine:

    def __init__(self, filters):
        self.filters = filters
        self.keyword_mode = filters.get("keyword_mode", "any")
        self.keywords = filters.get("keywords", {})
        self.action_keys = filters.get("action_keys", [])
        self.owner_states = filters.get("owner_states", [])
        self.legal_entity_codes = filters.get("legal_entity_codes", [])

    def filter_trademarks(self, trademarks):
        filtered = []
        for tm in trademarks:
            matches, reasons = self.matches_filters(tm)
            if matches:
                tm["match_reasons"] = reasons
                filtered.append(tm)
        return filtered

    def matches_filters(self, trademark):
        reasons = []

        if self.owner_states:
            if trademark.get("stateCountryCode", "") not in self.owner_states:
                return False, []

        if self.legal_entity_codes:
            if trademark.get("entityTypeCode", "") not in self.legal_entity_codes:
                return False, []

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

    def _check_keywords(self, trademark):
        matches = []

        mark_kw = self.keywords.get("mark_identification", [])
        if mark_kw:
            mark_id = trademark.get("markIdentification", "")
            if self._text_matches_patterns(mark_id, mark_kw):
                matches.append(f"Mark Identification: {mark_id}")

        gs_kw = self.keywords.get("goods_services", [])
        if gs_kw:
            gs = trademark.get("goodsServices", "")
            if self._text_matches_patterns(gs, gs_kw):
                matches.append("Goods/Services match")

        owner_kw = self.keywords.get("owner_name", [])
        if owner_kw:
            owner = trademark.get("ownerName", "")
            dba = trademark.get("dbaAkaFormerly", "")
            if self._text_matches_patterns(owner, owner_kw):
                matches.append(f"Owner Name: {owner}")
            elif dba and self._text_matches_patterns(dba, owner_kw):
                matches.append(f"DBA/AKA Name: {dba}")

        email_kw = self.keywords.get("email_addresses", [])
        if email_kw:
            all_emails = (trademark.get("attorneyEmailAddresses", [])
                          + trademark.get("correspondantEmailAddresses", []))
            for email in all_emails:
                if self._text_matches_patterns(email, email_kw):
                    matches.append(f"Email: {email}")
                    break

        return matches

    def _text_matches_patterns(self, text, patterns):
        if not text or not patterns:
            return False
        text_lower = text.lower()
        for pattern in patterns:
            pattern_lower = pattern.lower()
            escaped = re.escape(pattern_lower)
            regex_pattern = f"^{escaped.replace(chr(92) + '*', '.*')}$"
            try:
                if re.search(regex_pattern, text_lower):
                    return True
            except re.error:
                if pattern_lower.replace("*", "") in text_lower:
                    return True
        return False


# --- email content ---

def escape_html(text):
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def create_email_html(matches, batch_info):
    num_matches = len(matches)
    start_sn = batch_info.get("start_sn", "N/A")
    end_sn = batch_info.get("end_sn", "N/A")
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{TRADEMARK_CSS}</style></head>
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
        sn = tm.get("serialNumber", "N/A")
        tsdr_url = f"https://tsdr.uspto.gov/#caseNumber={sn}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch"

        html += f"""
        <div class="trademark">
            <div class="trademark-header">Match #{i} - Serial Number: {sn}</div>
            <div class="field" style="text-align: center; margin: 15px 0; padding: 15px; background-color: #e8f4f8; border: 1px solid #b3dce6; border-radius: 5px;">
                <a href="{tsdr_url}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #003366; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">View Trademark Details</a>
            </div>"""

        if tm.get("markIdentification"):
            html += f'<div class="field"><span class="field-label">Mark:</span><span class="field-value">{escape_html(tm["markIdentification"])}</span></div>'
        if tm.get("ownerName"):
            html += f'<div class="field"><span class="field-label">Owner:</span><span class="field-value">{escape_html(tm["ownerName"])}</span></div>'
        if tm.get("status"):
            html += f'<div class="field"><span class="field-label">Status:</span><span class="field-value">{escape_html(tm["status"])}</span></div>'
        if tm.get("filingDate"):
            html += f'<div class="field"><span class="field-label">Filing Date:</span><span class="field-value">{tm["filingDate"]}</span></div>'
        if tm.get("stateCountryCode") or tm.get("isoCode"):
            html += f'<div class="field"><span class="field-label">Location:</span><span class="field-value">{tm.get("stateCountryCode", "")} {tm.get("isoCode", "")}</span></div>'
        if tm.get("entityTypeCode"):
            html += f'<div class="field"><span class="field-label">Entity Type Code:</span><span class="field-value">{tm["entityTypeCode"]}</span></div>'

        attorney_emails = tm.get("attorneyEmailAddresses", [])
        if attorney_emails:
            html += f'<div class="field"><span class="field-label">Attorney Email(s):</span><span class="field-value">{", ".join(attorney_emails)}</span></div>'

        correspondant_emails = tm.get("correspondantEmailAddresses", [])
        if correspondant_emails:
            html += f'<div class="field"><span class="field-label">Correspondant Email(s):</span><span class="field-value">{", ".join(correspondant_emails)}</span></div>'

        if tm.get("goodsServices"):
            html += f'<div class="field"><span class="field-label">Goods/Services:</span><span class="field-value">{escape_html(tm["goodsServices"][:500])}</span></div>'

        match_reasons = tm.get("match_reasons", [])
        if match_reasons:
            html += '<div class="match-reasons"><strong>Match Reasons:</strong><ul>'
            for reason in match_reasons:
                html += f"<li>{escape_html(reason)}</li>"
            html += "</ul></div>"

        html += f"""
            <div class="field" style="margin-top: 15px;">
                <a href="{tsdr_url}" target="_blank" style="color: #003366; text-decoration: none; font-weight: bold;">View on USPTO TSDR</a>
            </div>
        </div>"""

    html += f"""
        <div class="footer">
            <p>Total trademarks processed across this batch: {batch_info.get('total_processed', 0)}</p>
        </div>
    </body>
    </html>"""
    return html


# --- work function ---

def trademark_work(cfg, state, session, output_dir, log):
    if not state:
        state = {"last_processed_sn": 0, "total_matches": 0, "total_batches_processed": 0}

    api_key = cfg.get("trademark_api_key")
    if not api_key:
        log.error("trademark_api_key not found in config")
        return None

    rate_limit = get_rate_limit(cfg, log)
    client = USPTOClient(session, api_key, rate_limit_delay=rate_limit)
    filter_engine = FilterEngine(cfg.get("trademark_filters", {}))

    batch_size = cfg.get("trademark_batch_size", 20)
    max_empty = cfg.get("trademark_max_empty_batches", 3)
    max_results = cfg.get("trademark_max_results_per_email", 100)

    start_sn = get_next_sn(state)
    log.info(f"Starting from Serial No.: {start_sn}")

    current_sn = start_sn
    empty_batch_count = 0
    all_matches = []
    total_processed = 0

    while True:
        batch_sns = list(range(current_sn, current_sn + batch_size))
        log.info(f"Querying batch: {batch_sns[0]} - {batch_sns[-1]}")

        response = client.query_batch(batch_sns)
        if response is None:
            log.error("API failed")
            break

        trademarks = client.extract_trademark_data(response)
        log.info(f"  Found {len(trademarks)} trademark applications")

        if len(trademarks) == 0:
            empty_batch_count += 1
            log.info(f"  Empty batch ({empty_batch_count}/{max_empty})")
            if empty_batch_count >= max_empty:
                log.info(f"Reached end of data after {max_empty} empty batches")
                last_valid = current_sn - (batch_size * empty_batch_count)
                state = update_position(state, last_valid, "no_data")
                break
        else:
            empty_batch_count = 0
            total_processed += len(trademarks)

            matches = filter_engine.filter_trademarks(trademarks)
            if matches:
                log.info(f"  Captured {len(matches)} hits")
                all_matches.extend(matches)
                last_match_sn = matches[-1].get("serialNumber", current_sn + batch_size - 1)
                state = update_position(state, last_match_sn, "match_found")
            else:
                log.info("  No matches")

        batch_end_sn = batch_sns[-1]
        state = update_position(state, batch_end_sn, "batch_complete")

        if len(all_matches) >= max_results:
            log.info(f"Hit max results per email ({max_results})")
            _send_digest(cfg, all_matches, start_sn, batch_end_sn, total_processed, output_dir, log)
            all_matches = []
            start_sn = batch_end_sn + 1

        current_sn += batch_size

    if all_matches:
        final_sn = current_sn - 1
        _send_digest(cfg, all_matches, start_sn, final_sn, total_processed, output_dir, log)

    return state


def _send_digest(cfg, matches, start_sn, end_sn, total_processed, output_dir, log):
    batch_info = {
        "start_sn": start_sn,
        "end_sn": end_sn,
        "total_processed": total_processed,
    }
    subject = f"{cfg.get('email_subject_prefix', 'Trademark Alert:')} {len(matches)} New Match(es) Found"
    html = create_email_html(matches, batch_info)
    fallback_path = output_dir / f"matches_{start_sn}_{end_sn}.json"
    send_or_save(cfg, subject, html, None, matches, fallback_path, log)


# --- main ---

def main():
    cfg = load_config()
    try:
        run_monitor(cfg, trademark_work)
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        logging.getLogger(__name__).exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
