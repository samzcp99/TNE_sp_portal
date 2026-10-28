'use strict';
// Shared pure helpers, exported for offline tests and used by the mobile form.
(function(root){
 function email(value){
  const normalized=value.normalize('NFKC').trim();
  const parts=normalized.split('@');
  if(parts.length!==2||normalized.length>254)return {error:'请填写完整邮箱，例如 name@example.com。'};
  const [local,domain]=parts;
  if(!local||local.length>64||local.startsWith('.')||local.endsWith('.')||local.includes('..')||!/^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$/.test(local))return {error:'邮箱用户名格式不正确，请检查空格、句点或非法字符。'};
  const labels=domain.split('.');
  if(labels.length<2||!/^[A-Za-z]{2,63}$/.test(labels.at(-1)))return {error:'邮箱域名不完整，请检查 @ 后面的内容。'};
  if(labels.some(label=>!/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/.test(label)))return {error:'邮箱域名格式不正确，请检查空格或拼写。'};
  return {value:local+'@'+domain.toLowerCase()};
 }
 function mobile(value,country,phoneLibrary){
  let compact=value.normalize('NFKC').trim().replace(/[ ()-]/g,'');
  if(!/^\+?[0-9]+$/.test(compact))return {error:'电话只能填写数字和国家区号，请检查是否混入其他字符。'};
  if(country==='CN'){
   if(compact.startsWith('+86'))compact=compact.slice(3);
   else if(compact.length===13&&compact.startsWith('86'))compact=compact.slice(2);
   if(!/^1[3-9][0-9]{9}$/.test(compact))return {error:'大陆手机号需为 1 开头的 11 位数字，请检查是否多填或少填。'};
   return {value:'+86'+compact,national:compact};
  }
  if(country==='OTHER'&&!compact.startsWith('+'))return {error:'其他地区请填写完整的 +国家区号和电话号码。'};
  if(!phoneLibrary)return {error:'号码校验组件未加载，请刷新页面后重试。'};
  try{
   const parsed=phoneLibrary.parsePhoneNumberFromString(compact,{defaultCountry:country==='OTHER'?undefined:country,extract:false});
   if(!parsed||!parsed.isPossible()||!parsed.isValid())return {error:'号码格式或位数不符合所选地区要求，请检查号码和区号。'};
   if(country!=='OTHER'&&parsed.countryCallingCode!==phoneLibrary.getCountryCallingCode(country))return {error:'号码中的国家区号与所选地区不一致。'};
   if(parsed.countryCallingCode==='86')return mobile(parsed.number,'CN',phoneLibrary);
   return {value:parsed.number};
  }catch{return {error:'电话号码格式不正确，请检查国家区号和号码。'};}
 }
 const api={email,mobile};
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.ContactValidation=api;
})(typeof window==='undefined'?globalThis:window);
