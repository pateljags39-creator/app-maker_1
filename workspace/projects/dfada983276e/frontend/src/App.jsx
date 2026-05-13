import React, {useEffect, useState} from 'react';
export default function App(){
  const [notes,setNotes]=useState([]);
  useEffect(()=>{fetch('/api/notes').then(r=>r.json()).then(setNotes)},[]);
  return <ul>{notes.map(n=><li key={n.id}>{n.text}</li>)}</ul>;
}
