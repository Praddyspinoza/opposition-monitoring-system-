window.SENATE_DATA=JSON.parse(fflate.strFromU8(fflate.gunzipSync(Uint8Array.from(atob(window.SENATE_PARTS.join('')),c=>c.charCodeAt(0)))));delete window.SENATE_PARTS;
