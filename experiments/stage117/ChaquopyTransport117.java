package com.exvius.local;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
/** Source-only Android adapter. Caller must establish a private fixture and start isolated Python. */
final class ChaquopyTransport117 implements Session117.Transport {
 public String commit(String root,String pid,String token,String binding,byte[] proposal,Session117.Witness witness)throws Exception{
  try(PyObject module=Python.getInstance().getModule("commit117");PyObject reply=module.callAttr("commit_android",root,pid,token,binding,proposal,witness)){return reply.toString();}
 }
}
