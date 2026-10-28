"""Offline contact format checks; these do not prove ownership or reachability."""
import re
import unicodedata
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import phonenumbers

COUNTRIES = {'CN','NZ','AU','GB','US','OTHER'}


def normalize_mobile(value, country=''):
    value = unicodedata.normalize('NFKC', value).strip()
    if not re.fullmatch(r'\+?[0-9 ()-]+',value):
        raise ValueError('联系电话只能包含数字、区号、空格、括号或短横线。')
    if country and country not in COUNTRIES:
        raise ValueError('请选择有效的电话国家区号。')
    compact = re.sub(r'[ ()-]','',value)
    if country == 'CN':
        if compact.startswith('+86'):
            compact = compact[3:]
        elif len(compact)==13 and compact.startswith('86'):
            compact = compact[2:]
        if not re.fullmatch(r'1[3-9][0-9]{9}',compact):
            raise ValueError('中国大陆手机号必须是 1 开头的 11 位数字，请检查是否多填或少填。')
        return '+86'+compact
    if not compact.startswith('+') and (not country or country=='OTHER'):
        raise ValueError('请选择国家区号；其他地区号码需填写完整的 +国家区号和号码。')
    try:
        parsed=phonenumbers.parse(compact, country if country and country!='OTHER' else None)
    except phonenumbers.NumberParseException as exception:
        raise ValueError('联系电话格式不正确，请检查国家区号和号码。') from exception
    if country and country!='OTHER' and parsed.country_code!=phonenumbers.country_code_for_region(country):
        raise ValueError('号码中的国家区号与所选地区不一致。')
    if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(parsed):
        raise ValueError('电话号码格式或位数不符合所选地区要求，请检查是否漏填或多填。')
    if parsed.country_code==86:
        return normalize_mobile(phonenumbers.format_number(parsed,phonenumbers.PhoneNumberFormat.E164),'CN')
    return phonenumbers.format_number(parsed,phonenumbers.PhoneNumberFormat.E164)


def normalize_email(value, confirmation):
    value=unicodedata.normalize('NFKC',value).strip()
    confirmation=unicodedata.normalize('NFKC',confirmation).strip()
    def canonical_domain(address):
        if address.count('@')!=1:
            return address
        local,domain=address.rsplit('@',1)
        return local+'@'+domain.lower()
    value,confirmation=canonical_domain(value),canonical_domain(confirmation)
    if value!=confirmation:
        raise ValueError('两次填写的私人邮箱不一致，请核对。')
    if len(value)>254 or value.count('@')!=1:
        raise ValueError('请填写完整邮箱，例如 name@example.com。')
    local,domain=value.rsplit('@',1)
    if (not local or len(local)>64 or local.startswith('.') or local.endswith('.')
            or '..' in local or not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+',local)):
        raise ValueError('邮箱用户名格式不正确，请检查空格、连续句点或非法字符。')
    labels=domain.split('.')
    if len(labels)<2 or not re.fullmatch(r'[A-Za-z]{2,63}',labels[-1]):
        raise ValueError('邮箱域名不完整，例如应填写 qq.com 或 outlook.com。')
    if any(not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',label) for label in labels):
        raise ValueError('邮箱域名格式不正确，请检查空格或拼写。')
    return local+'@'+domain.lower()
