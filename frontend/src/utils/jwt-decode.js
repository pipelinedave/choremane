/**
 * A simple JWT decode implementation to replace the jwt-decode package
 * 
 * This is a simplified version that only handles base64url decoding of the token's payload
 */

function b64DecodeUnicode(str) {
  // Add padding if needed
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) {
    str += '=';
  }
  
  return decodeURIComponent(
    atob(str)
      .split('')
      .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
      .join('')
  );
}

export default function jwtDecode(token) {
  if (!token) {
    throw new Error('Invalid token specified');
  }
  
  const parts = token.split('.');
  
  if (parts.length !== 3) {
    throw new Error('JWT must have 3 parts');
  }
  
  try {
    // Only decode the payload (middle part)
    const payload = b64DecodeUnicode(parts[1]);
    return JSON.parse(payload);
  } catch (e) {
    throw new Error('Invalid token specified: ' + e.message);
  }
}
