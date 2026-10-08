const fs = require('fs');
const katex = require(process.argv[2]);
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  const results = JSON.parse(input).map(f => {
    try {
      if (!f.latex) throw new Error('需要人工转录 LaTeX');
      katex.renderToString(f.latex, {throwOnError:true, trust:false, strict:'error', maxExpand:1000});
      return {id:f.id,valid:true,semantic_verified:false};
    } catch(e) { return {id:f.id,valid:false,error:e.message,semantic_verified:false}; }
  });
  process.stdout.write(JSON.stringify(results));
});
